#!/usr/bin/env python

import datetime
import os
import random
import re
import string
import sys
import wsgiref.handlers

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
  priority = db.StringProperty(required=True,choices = set(["asap","soon","sometime"]))
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
      todos = db.GqlQuery("SELECT * from Todo ORDER BY created DESC");
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
  def get(self,slug=0):
      todos = db.GqlQuery("SELECT * from Todo ORDER BY created DESC");
      q = Todo.all()
      q.filter('slug =',slug) 
      md = markdown.Markdown()
      res = q.fetch(1)
      for todo in res:
          self.generate('todo.html', {
              'todo_title': todo.todo_title,
              'todo_text': md.convert(todo.todo_text),
              'todos': todos,
          })

def main():
  application = webapp.WSGIApplication([
    ('/', TodosPage),
    ('/todos', TodosPage),
    ('/todo/(.*)', TodoPage),
  ], debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
