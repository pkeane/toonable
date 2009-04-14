from xml.etree import cElementTree as ET
import os
import re
import time
import httplib2

ATOM_NS = '{http://purl.org/atom/ns#}'
APP_NS = '{http://www.w3.org/2007/app}'
XHTML_NS = '{http://www.w3.org/1999/xhtml}'

def rfc3339():
    """
    Format a date the way Atom likes it (RFC3339)
    """
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')

def _dirify(str):
    str = re.sub('\&amp\;|\&', ' and ', str) 
    str = re.sub('[-\s]+', '_', str)
    return re.sub('[^\w\s-]', '', str).strip().lower()

def _indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for e in elem:
            _indent(e, level+1)
        if not e.tail or not e.tail.strip():
            e.tail = i
    if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

class Atom:
    def addElement(self,tagname,text='',ns=''):
        if ns:
            elem = ET.SubElement(self.root,ns+tagname)
        else:
            elem = ET.SubElement(self.root,tagname)
        if text:
            elem.text = text
        return elem

    def addChildElement(self,parent,tagname,text='',ns=''): 
        if ns:
            elem = ET.SubElement(parent,ns+tagname)
        else:
            elem = ET.SubElement(parent,tagname)
        if text:
            elem.text = text

    @classmethod
    def from_text(self,text):
        atom = ET.XML(text)
        if atom.tag == ATOM_NS + "feed":
            return Feed(atom)
        elif atom.tag == ATOM_NS + "entry":
            return Entry(atom)
        raise IOError("not an atom document")


    @classmethod
    def retrieve(self,url,user='',passwd=''):
        h = httplib2.Http()
        if user and passwd:
            h.add_credentials(user,passwd)
        resp, content = h.request(url)
        atom = ET.XML(content)
        if atom.tag == ATOM_NS + "feed":
            return Feed(atom)
        elif atom.tag == ATOM_NS + "entry":
            return Entry(atom)
        raise IOError("not an atom document")

    def __getattr__(self, name):
        try:
            method = getattr(self,'get'+ name.capitalize())
        except:
            return
        else:
            if callable(method): 
                return method() 
            else:  raise AttributeError, name

    def getText(self,elem,root=None):
        if root:
            txt = root.findtext(ATOM_NS+elem)
        else:
            txt = self.root.findtext(ATOM_NS+elem)
        if txt:
            return txt.encode('utf-8')

    def setId(self,text):
        self.addElement('id',text)

    def getId(self):
        return self.getText('id')

    def setTitle(self,text):
        self.addElement('title',text)

    def getTitle(self):
        return self.getText('title')

    def setUpdated(self,text=''):
        if not text:
            text = rfc3339()
        self.addElement('updated',text)

    def getUpdated(self):
        return self.getText('updated')

    def setRights(self,text):
        self.addElement('rights',text)

    def getRights(self):
        return self.getText('rights')

    def addLink(self,href,rel='',type='',length='',title=''):
        link = self.addElement('link')
        link.set('href',href)
        if rel:
            link.set('rel',rel)
        if type:
            link.set('type',type)
        if length:
            link.set('length',rel)
        if title:
            link.set('title',title)
        return link

    def getLinks(self):
        links = []
        for link in self.root.getiterator(ATOM_NS+'link'):
            ln = {}
            ln['href'] = link.get('href')
            ln['rel'] = link.get('rel')
            ln['title'] = link.get('title')
            ln['type'] = link.get('type')
            ln['length'] = link.get('length')
            links.append(ln)
        return links

    def getAlt(self):
        for link in self.getLinks():
            if 'alternate' == link['rel']:
                return link['href']
        return 'no-alt'

    def addCategory(self,term,scheme='',label='',text=''):
        category = self.addElement('category')
        category.set('term',term)
        if scheme:
            category.set('scheme',scheme)
        if label:
            category.set('label',label)
        if text:
            category.text = text

    def getCategories(self,scheme=''):
        categories = []
        for category in self.root.getiterator(ATOM_NS+'category'):
            cat = {}
            cat['term'] = category.get('term')
            cat['scheme'] = category.get('scheme')
            cat['label'] = category.get('label')
            if category.text:
                cat['text'] = category.text.encode('utf-8')
            if scheme:
                if scheme == cat['scheme']:
                    categories.append(cat)
            else: categories.append(cat)
        return categories

    def addAuthor(self,name='',uri='',email=''):
        author = self.addElement('author')
        if not name:
            name = 'DASe (Digital Archive Services)'
            uri = 'http://daseproject.org'
            email = 'admin@daseproject.org'
        self.addChildElement(author,'name',name)
        if uri: 
            self.addChildElement(author,'uri',uri)
        if email:
            self.addChildElement(author,'email',email)
        return author

    def getAuthors(self):
        authors = []
        auth = {}
        for author in self.root.getiterator(ATOM_NS+'author'):
            auth['name'] = self.getText('name',author)
            auth['uri'] = self.getText('uri',author)
            auth['email'] = self.getText('email',author)
            authors.append(auth)
        return authors

    def asXml(self):
        _indent(self.root)
        return ET.tostring(self.root).replace('ns0','d').encode('utf-8') 


class Feed(Atom):
    def __init__(self,root=''):
        if root:
            self.root = root 
        else:
            self.root = ET.Element("feed", xmlns='http://www.w3.org/2005/Atom')

    def setGenerator(self,text,uri='',version=''):
        gen = self.addElement('generator',text)
        if (uri):
            gen.set(uri)
        if (version):
            gen.set(version)
        return gen

    def getGenerator(self):
        generator = self.root.find(ATOM_NS+'generator')
        set = {}
        if generator:
            set['name'] = self.getText('generator') 
            set['uri'] = generator.get('uri')
            set['version'] = generator.get('version')
            return set

    def setIcon(self,text):
        self.addElement('icon',text)

    def getIcon(self):
        return self.getText('icon')

    def setSubtitle(self,text):
        self.addElement('subtitle',text)

    def getSubtitle(self):
        return self.getText('subtitle')

    def getEntries(self):
        entries = []
        for entry in self.root.getiterator(ATOM_NS+'entry'):
            entries.append(Entry(entry))
        return entries


class Entry(Atom):
    def __init__(self,root=''):
        if root:
            self.root = root
        else:
            self.root = ET.Element("entry", xmlns='http://www.w3.org/2005/Atom')

    def setPublished(self,text):
        self.addElement('published',text)

    def getPublished(self):
        return self.getText('published')

    def setContent(self,text,type='text'):
        content = self.addElement('content')
        content.set('type',type)
        content.text = text
        return content

    def getContent(self):
        return self.getText('content')

    def getSummary(self):
        return self.getText('summary')
