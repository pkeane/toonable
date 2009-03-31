#!/usr/bin/env python

import datetime
import markdown
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

def slugify(inStr):
    removelist = ["a", "an", "as", "at", "before", "but", "by", "for","from","is", "in", "into", "like", "of", "off", "on", "onto","per","since", "than", "the", "this", "that", "to", "up", "via","with"];
    for a in removelist:
        aslug = re.sub(r'\b'+a+r'\b','',inStr)
    aslug = re.sub('[^\w\s-]', '', aslug).strip().lower()
    aslug = re.sub('\s+', '-', aslug)
    return aslug

class Todo(db.Model):
  """Represents a single todo.
  """
  todo_title = db.TextProperty(required=True)
  todo_text = db.TextProperty(required=True)
  slug = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

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
      'application_name': 'Simple Todopad',
    }
    values.update(template_values)
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates', template_name))
    self.response.out.write(template.render(path, values, debug=_DEBUG))

class TodosPage(BaseRequestHandler):
  """Lists the todos """

  @login_required
  def get(self,id=0):
      todos = db.GqlQuery("SELECT * from Todo ORDER BY created DESC");
      self.generate('index.html', {
          'todos': todos,
      })

  def post(self):
      todo_title = self.request.get('todo_title')
      todo_text =  self.request.get('todo_text')
      slug = slugify(todo_title) 
      if (todo_text and todo_title):
          record = Todo(todo_title=todo_title,todo_text=todo_text,slug=slug);
          record.put()
      self.redirect('/')

class TodoEditPage(BaseRequestHandler):
  @login_required
  def get(self,key=0):
      todos = db.GqlQuery("SELECT * from Todo ORDER BY created DESC");
      todo = Todo.get(key)
      self.generate('edit.html', {
          'todo_title': todo.todo_title,
          'todo_text': todo.todo_text,
          'todo_key': key,
          'todos' : todos,
      })

  def post(self,key=0):
      todo = Todo.get(key)
      todo.todo_title = self.request.get('todo_title')
      todo.todo_text =  self.request.get('todo_text')
      todo.slug = slugify(todo.todo_title) 
      todo.put()
      self.redirect('/todo/'+todo.slug)

class TodoTextPage(BaseRequestHandler):
  def get(self,slug=0):
      q = Todo.all()
      q.filter('slug =',slug) 
      md = markdown.Markdown()
      res = q.fetch(1)
      for todo in res:
          self.generate('todo_text.html', {
              'todo_title': todo.todo_title,
              'todo_text': md.convert(todo.todo_text),
          })

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
    ('/edit/(.*)', TodoEditPage),
    ('/text/(.*)', TodoTextPage),
    ('/todo/(.*)', TodoPage),
  ], debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
