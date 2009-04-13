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

class Todo(db.Model):
  """Represents a single todo.
  """
  text = db.StringProperty(required=True)
  priority = db.StringProperty(required=True,choices = set(["a1asap","a2soon","a3sometime"]))
  created = db.DateTimeProperty(auto_now_add=True)

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
      todos = db.GqlQuery("SELECT * from Todo ORDER BY priority")
      #use oauth here
      self.generate('index.html', {
          'todos': todos,
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
    SERVER = 'www.google.com'
    PORT = 80
    REQUEST_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetRequestToken'
    ACCESS_TOKEN_URL = 'https://www.google.com/accounts/OAuthGetAccessToken'
    AUTHORIZATION_URL = 'https://www.google.com/accounts/OAuthAuthorizeToken'
    CALLBACK_URL = 'http://toonable.appspot.com'
    RESOURCE_URL = 'https://mail.google.com/mail/feed/atom'
    SCOPE = 'https://mail.google.com/mail/feed/atom'
    CONSUMER_KEY = 'toonable.appspot.com'  
    CONSUMER_SECRET = 'NdT5Uuut1ze6HYyRfFa+J3i0'
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
        self.response.out.write(oauth.OAuthToken.from_string(result.content))

def main():
  application = webapp.WSGIApplication([
    ('/', TodosPage),
    ('/todos', TodosPage),
    ('/todo/(.*)', TodoPage),
    ('/oauth', OAuthPage),
  ], debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
