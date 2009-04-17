#!/usr/bin/env python

import atomlib.atom03
import datetime
import os
import random
import re
import string
import sys
import wsgiref.handlers

import time
import oauth.oauth as oauth 

from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

REQUEST_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetRequestToken'
ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'
AUTHORIZATION_URL = 'https://www.google.com/accounts/OAuthAuthorizeToken'
CALLBACK_URL = 'http://toonable.appspot.com/oauth/token_ready'
RESOURCE_URL = 'https://mail.google.com/mail/feed/atom'
SCOPE = 'https://mail.google.com/mail/feed/atom'
CONSUMER_KEY = 'toonable.appspot.com'  
CONSUMER_SECRET = 'NdT5Uuut1ze6HYyRfFa+J3i0'

class Project(db.Model):
  name = db.StringProperty(required=True)

class Context(db.Model):
  name = db.StringProperty(required=True)

class Todo(db.Model):
  """Represents a single todo.
  """
  text = db.StringProperty(required=True)
  priority = db.StringProperty(required=True,choices = set(["a1asap","a2soon","a3sometime"]))
  created = db.DateTimeProperty(auto_now_add=True)
  project = db.ReferenceProperty(Project)
  context = db.ReferenceProperty(Context)

class Mail(db.Model):
  text = db.TextProperty(required=True)

class OAuthToken(db.Model):
    user = db.UserProperty()
    token_key = db.StringProperty(required=True)
    token_secret = db.StringProperty(required=True)
    type = db.StringProperty(required=True)
    scope = db.StringProperty(required=True)

class BaseRequestHandler(webapp.RequestHandler):
  """Supplies a common template generation function.

  When you call generate(), we augment the template variables supplied with
  the current user in the 'user' variable and the current webapp request
  in the 'request' variable.
  """
  def generate(self, template_name, template_values={}):
    values = {
      'request': self.request,
      'user': users.GetCurrentUser(),
      'login_url': users.CreateLoginURL(self.request.uri),
      'logout_url': users.CreateLogoutURL('http://' + self.request.host + '/'),
      'debug': self.request.get('deb'),
      'application_name': 'Toonable Tasks',
    }
    values.update(template_values)
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates', template_name))
    self.response.out.write(template.render(path, values, debug=_DEBUG))

class TodosPage(BaseRequestHandler):
  """Lists the todos """

  @login_required
  def get(self):
      cache=False
      mail_feed = ''
      if self.request.get('usecache'):
          mail_feed = atomlib.atom03.Atom.from_text(Mail.all().get().text.encode("utf-8"))
          cache=True
      else:
          t = OAuthToken.all()
          t.filter("user =",users.GetCurrentUser())
          t.filter("scope =", SCOPE)
          t.filter("type =", 'access')
          results = t.fetch(1)
          for oauth_token in results:
              if oauth_token.token_key:
                  key = oauth_token.token_key
                  mail_feed = oauth_token.token_key
                  secret = oauth_token.token_secret
                  token = oauth.OAuthToken(key,secret)
                  consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
                  oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
                                                                             token=token,
                                                                             http_url=SCOPE)
                  signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
                  oauth_request.sign_request(signature_method, consumer, token)
                  result = urlfetch.fetch(url=SCOPE,
                                          method=urlfetch.GET,
                                          headers=oauth_request.to_header())
                  mail_feed = atomlib.atom03.Atom.from_text(result.content) 
                  m = Mail.all().get()
                  if m:
                      m.text = db.Text(result.content,"utf-8")
                  else:
                      m = Mail(text=unicode(result.content,"utf-8"))
                  m.put()
                  if not oauth_token:
                      self.redirect('/oauth')
      todos = db.GqlQuery("SELECT * from Todo ORDER BY priority, created DESC")
      self.generate('index.html', {
          'cache': cache,
          'todos': todos,
          'mail_feed' : mail_feed,
      })

  def post(self):
      text = self.request.get('text')
      priority =  self.request.get('priority')
      if (text and priority):
          record = Todo(text=text,priority=priority);
          record.put()
      self.redirect('/')

class TodoPage(BaseRequestHandler):

  def delete(self,key=''):
      todo = Todo.get(key);
      todo.delete()
      self.redirect('/')

class OAuthPage(BaseRequestHandler):

  def get(self):
    scope = {'scope':SCOPE}
    consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
    oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
                                                               token=None,
                                                               http_url=REQUEST_TOKEN_URL,parameters=scope)
    signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
    oauth_request.sign_request(signature_method, consumer, None)
    url = oauth_request.to_url() 
    result = urlfetch.fetch(url)
    if result.status_code == 200:
        token = oauth.OAuthToken.from_string(result.content) 
        #persist token
        saved_token = OAuthToken(user=users.GetCurrentUser(),
                                 token_key = token.key,
                                 token_secret = token.secret,
                                 scope = SCOPE,
                                 type = 'request',
                                )
        saved_token.put()
        #now authorize token
        oauth_request = oauth.OAuthRequest.from_token_and_callback(token=token,
                                                                   callback=CALLBACK_URL,
                                                                  http_url=AUTHORIZATION_URL)
        url = oauth_request.to_url() 
        self.redirect(url)
    else:
      self.response.out.write('no request token')


class OAuthReadyPage(BaseRequestHandler):

  def get(self):
      t = OAuthToken.all()
      t.filter("user =",users.GetCurrentUser())
      t.filter("token_key =", self.request.get('oauth_token'))
      t.filter("scope =", SCOPE)
      t.filter("type =", 'request')
      results = t.fetch(1)
      for oauth_token in results:
          if oauth_token.token_key:
              key = oauth_token.token_key
              secret = oauth_token.token_secret
              token = oauth.OAuthToken(key,secret)
              #get access token
              consumer = oauth.OAuthConsumer(CONSUMER_KEY, CONSUMER_SECRET)
              oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer,
                                                                 token=token,
                                                                 http_url=ACCESS_TOKEN_URL)
              signature_method = oauth.OAuthSignatureMethod_HMAC_SHA1()
              oauth_request.sign_request(signature_method, consumer, token)
              url = oauth_request.to_url() 
              result = urlfetch.fetch(url)
              if result.status_code == 200:
                  token = oauth.OAuthToken.from_string(result.content) 
                  oauth_token.token_key = token.key
                  oauth_token.token_secret = token.secret
                  oauth_token.type = 'access'
                  oauth_token.put()
                  self.redirect('/')
              else:
                  self.response.out.write(result.content)
          else:
                  self.response.out.write('no go')



def main():
  application = webapp.WSGIApplication([
    ('/', TodosPage),
    ('/todos', TodosPage),
    ('/todo/(.*)', TodoPage),
    ('/oauth', OAuthPage),
    ('/oauth/token_ready', OAuthReadyPage),
  ], debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
