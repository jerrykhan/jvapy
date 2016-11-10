#! /usr/bin/env python
# vim: set fileencoding=Latin-1
"""
TITLE  : xml class wrapper for minidom to highly simplify xml access path.
AUTOR  : J.Vacher.

OBJECTIF : all xml wrappers propose a complexe structure manipulation to read or write xml file where often .. you just require simple things..
  I propose to dynamically navigate into an XML file as you acces a python instances tree to quickly read or update an XML data from a string or a file

  Create the instance : x = xml(fn=myfile.xml)
  then play with it:
    print (x.Element1__1.Element2__1.Attribute)

HISTORIC :
   18 juillet 2016    : J.Vacher : Creation

INTERFACES :

REQUIREMENTS:
   - Read an xml file from string at init
   - Read an xml file from file at init
   - Create an empty xml file at init

   - XML element are : prolog, Element, attribute, comment
   - Navigate to any XML element through root.Ename.AttName
   - Update any attribute via root.Ename.AttName = value
   - reuse list functions : append, pop, for, expand, delete for each Element nodes to CRUD them

   - Save the XML file, (eventually any node)

CONSTRAINTS:
   - no Element name starting with _ !
   - no Attribute name starting with _ !
   => All these must be python internal variables !
   - no Element or Attributes with a name containing '__'
   - If element has the tagName of an attribute ? what appends ?  => the attribute is in priority., use ElementName__0

MINIDOM DATA:
  different types: 
     Attributes               : Addressed simply as standard affectaion for an Element ex: root.Element.attribute = value
     CDATASection
     Comment                  : Should be addressed as a specifically formated TextNode 
     DocumentFragment
     Element                  : should be addressed by the list management commands: append, extend, insert, remove, clear, count,  
     ProcessingInstruction
     TextNode

QUESTIONS/ISSUES/ACTIONS:
   - How to manage prolog : TODO
   - How to manage NameSpaces : TODO
   - How to manage Errors : TODO
   - Traiter le cas d'un nouveau document auquel on fait newdoc.port = 8080 !

ETAT:
  Initial Dev OnGoing.
"""
__version__="0.1.3"
__module__="jva.file.xmljv"

import sys, os, re, time
# JVA TEMPLATE: Ce bloc est important pour permetre de rendre visible le package meme si l'utilisateur n'a pas correctement mis a jour son PYTHONPATH
if __name__ == '__main__':
  # Modification du sys.path si le package n'est pas reference. sys.path[0] donne le chemin du module courant
  #  Erreur du sys.path, si on est dans le repertoire courant '' est renvoye au lieu de '.' ce qui met a mal
  #  win32api.GetFullPathName() qui renvoie vide contre getcwd() au travers du abspath.
  if not sys.path[0]: sys.path[0] = '.'
  root_pkg = os.path.abspath(os.path.abspath(sys.path[0])+'/../..')
  if root_pkg not in map(os.path.abspath, sys.path):
    sys.path.insert(0,root_pkg)

V=0

from xml.dom import minidom

"""
Representation d'un node en liste: 
  des comparaisons on ne garde que == et !=
  __contains__ a etudier TODO
  __len__ __getitem__ __setitem__ 
  __delitem__ __getslice__ __setslice__ __delslice__
  __add__ __radd__ __iadd__ __mul__ __imul__
  append, insert, pop, remove, count, index, reverse, sort, extend
  => A implementer !!

"""


class xml: # Warning python 2 constraint !
    _Doms = {} # cached table of objects .. just to avoid creating tow object representing the same _dom object

    def __init__(s, parent=None, dom=None, isroot=0, fn=None, st=None):
        # These 2 lines ensure 
        if dom and s._Doms.has_key(id(dom)): s.__dict__ = s._Doms[id(dom)].__dict__ # singleton principle.
        else: s._Doms[id(dom)] = s

        s._isroot , s._dom = isroot , dom
        s._fn     , s._st   = fn     , st
        s._parent  = parent
        if not dom: 
          s._isroot = 1
          s._path = 'root'
        else:
          s._path = parent._path+"."+s._dom.nodeName
 
        s._indent, s._newl, s._encoding = '    ','\n',None

        s._creating = 0

        if dom: pass
        elif s._fn or s._st: 
          # on va passer par une chaine car je souhaite netoyer le fichier avant de le traiter.
          if s._fn: s._st = open(s._fn).read()
          # WARNING TODO doing that broke multi-lines comments elements.. and multi-line elements definition ... 
          # Maybe rework required ... should be good. initial idea was to avoid multi spaces/tab/returns that are stored by minidom parser.
          s._stclean = ''.join(re.split('[\t ]*\n[\t ]*',s._st))
          #s._stclean = s._st
          s._dom = minidom.parseString(s._stclean)
        else: s._dom = minidom.getDOMImplementation().createDocument(None,None,None)
    
    def __getattr__(s, att):
        if V:print ("TRACE getattr:"+att+" in "+s._path)
        #time.sleep(0.2)
        if att == '_data': 
            s.__dict__[att]= [xml(s,f) for f in s._dom.childNodes] 
            return getattr(s, att)
        
        # At this point we are managing XML contents
        tags = [f.nodeName for f in s._dom.childNodes] # nodeName plus universel que tagName XXX analyser l'impact
        try: atts = s._dom.attributes.keys()
        except AttributeError: atts = [] # peut etre voir a adresser le prologue dans le cas ou on est root.

        try:               ratt,fct = att.split('__')
        except ValueError: ratt,fct = att, None
        if fct:
            # fonction consistant a retourner la liste des elements
            if fct == 's': # il ne peut y avoir de list d'attributs de meme nom .. ignore. on ne traite que le cas des elements.
                if ratt in tags:  s.__dict__[att] = [xml(s,f) for f in s._dom.getElementsByTagName(ratt)]
                else: raise(AttributeError, att+" doesnot exist as element for listing in the current dom object: "+s._dom.nodeName)
            # fonction consistant a retourner le nombre d'elements.
            elif fct.isdigit(): # pareil
                if ratt in tags:
                    try: s.__dict__[att] = xml(s,s._dom.getElementsByTagName(ratt)[int(fct)])
                    except IndexError:
                        raise(AttributeError, att+" doesnot exist the current element list - IndexError: "+s._dom.nodeName)
                else: raise(AttributeError, att+" doesnot exist as element in the current dom object: "+s._dom.nodeName)
            else: # heu peut on avoir un pu..n d'attribut avec deux __ ??? ok admettons ... on fait comme i de rien n'etait
                if att in atts:    s.__dict__[att] = s._dom.getAttribute(att)
                elif att in tags:  s.__dict__[att] = xml(s,s._dom.getElementsByTagName(att)[0])
                else: raise(AttributeError, att+" doesnot exist as attribute nor element in the current dom object: "+s._dom.nodeName)
 
        else: # Nominal case .. simplest one.
            if att in atts:    s.__dict__[att] = s._dom.getAttribute(att)
            elif att in tags:  s.__dict__[att] = xml(s,s._dom.getElementsByTagName(att)[0])
            else: 
              # je traite le cas d'un potentiel nouvel element. on l'a pas trouve .. est on en train de le setter ?
              # on va positionner le flag et creer un objet  TODO
              #s._creating = 1
              #s._creating_dom = att
              #s._creating_root = s
              #s.__dict__[att] = xml(s,s._dom.getElementsByTagName(att))
              print "ERROR sur", att,
              print "dans",s._dom.nodeName,
              print s._path

              raise(AttributeError, att+" doesnot exist as attribute nor element in the current dom object: "+s._dom.nodeName)
        return getattr(s, att)

    def __setattr__(s, att, val):
        """Mise a jour d'une valeur
        """
        # question ... comment savoir si c'est un attributou un element ?
        # par defaut c'est un attribut un element doit s'ajouter... 
        if att[0] == '_': 
          if V: print ("TRACE setattr:"+att+'='+str(val)+" in "+s._path)
          s.__dict__[att] = val
        else: # ok seul le cas des attributs est traite ici l'Element doit preexister ! si pas le cas .. faut TODO
          if V: print ("TRACE setattr:"+att+'='+str(val)+" in "+s._path)
          #time.sleep(0.5)
          s._dom.setAttribute(att,str(val))
          s.__dict__[att] = str(val)

    def __delattr__(s, att):
        "when trying to remove an attribute which may be an element as well as an attribute."
        if V: print ("TRACE delattr:"+att+" in "+s._path)
        if att[0] == '_': del s.__dict__[att]  # internal variable management
        else:
            try: atts = s._dom.attributes.keys()
            except AttributeError: atts = [] # peut etre voir a adresser le prologue dans le cas ou on est root.
            if att in atts:
                try: del s.__dict__[att] # au pire on vient de le creer pour pouvoir l'effacer
                except KeyError: pass    # possible que l'on ai jamais construit l'attribut en question (delattr court-circuite getattr)  
                s._dom.removeAttribute(att)
            # TODO traiter le cas des elements ici

    def __len__(s): return len(s._data)
    def __getitem__(s, i): 
        try: return s._data[i]
        except TypeError: return getattr(s,i)
    def __setitem__(s, i, item): 
        if type(i) == type(1): 
            s._data[i] = item # TODO element a traiter
        else: # cas de mise a jour d'un attribut en mode dictionnaire
            s._dom.setAttribute(i,str(item))
            s.__dict__[i] = str(item)
    def __delitem__(s, i): 
        if type(i) == type(1): 
            del s._data[i] # TODO
        else: # cas de mise a jour d'un attribut en mode dictionnaire
            try: del s.__dict__[i] # au pire on vient de le creer pour pouvoir l'effacer
            except KeyError: pass    # possible que l'on ai jamais construit l'attribut en question (delattr court-circuite getattr)  
            s._dom.removeAttribute(i)
    
    # gestion des sous-listes type slice.
    def __getslice__(s, i, j):
        i = max(i, 0); j = max(j, 0)
        return s._data[i:j]
    def __setslice__(s, i, j, other):
        i = max(i, 0); j = max(j, 0)
        if isinstance(other, UserList):
            s._data[i:j] = other._data
        elif isinstance(other, type(s._data)):
            s._data[i:j] = other
        else:
            s._data[i:j] = list(other)
    def __delslice__(s, i, j):
        i = max(i, 0); j = max(j, 0)
        del s._data[i:j]

    # seen as a list ? we are talking about Elements !
    def append(s, object): print ('Not implemented')
    def insert(s, object): print ('Not implemented')
    def pop(s, object): print ('Not implemented')
    def remove(s, object): print ('Not implemented')
    def count(s, object): print ('Not implemented')
    def index(s, object): print ('Not implemented')
    def reverse(s, object): print ('Not implemented')
    def sort(s, object): print ('Not implemented')
    def extend(s, object): print ('Not implemented')

    # seen as a dictionnary ?: we are talking about attributes ! Warning not all methods available
    # Available : keys, values, items, haskey, getitem, setitem, delitem, getattr, setattr, delattr
    # Not Available: copy, update, clear, __len__, __cmp__, __repr__, iteritems, iterkeys, itervalues, get, setdefault, pop, popitem, fromkeys
    def keys(s):
        'Same as for a disctionary but returns attributes name list (warning XML specification does not constraint orders !)'
        return s._dom.attributes.keys()
    def values(s):
        '''Same as for a disctionary but returns attributes values list (warning! ) 
        XML specification does not constraint orders !
        The order is only relative to keys() result order.'''
        return [f.value for f in s._dom.attributes.values()]
    def items(s):
        'Same as for a disctionary but returns attributes key/value couple list'
        return s._dom.attributes.items()
    def has_key(s, k):
        'Same as for a disctionary but returns attributes name existence'
        return s._dom.attributes.has_key(k)
    # NOT Available for attribute dictionnary of minidom
    # def update(s, k): #TODO ?
    #    print ('Not implemented')
    # def iterkeys(s): return s._dom.attributes.iterkeys()
    # def itervalues(s): return s._dom.attributes.itervalues()
    # def iteritems(s): return s._dom.attributes.iteritems()

    def save(s, fnout=None, indent=None, newl=None, encoding=None):
        """Save as XML file, if fnout is None: use the fn property
        """
        if not s._fn: s._fn="/tmp/xmljv_default_output_file.xml"
        open(s._fn,'w').write(s.__str__(indent,newl,encoding))

    def __str__(s, indent=None, newl=None, encoding=None):
        """print the current XML object as a good well designed XML file
        """
        # Attention si on est root on prend tout .. si on est pas root on doit afficher le contenu de l'Element. 
        # rappel : seuls les elements sont des instances de la classe xml. 
        # ok .. TODO .. comment faire ? en fait il faut construire la chaine on pourrait la construire nominalement et retirer les tags courrants ?
        if indent   is None: indent   = s._indent
        if newl     is None: newl     = s._newl
        if encoding is None: encoding = s._encoding
        out = s._dom.toprettyxml(indent,newl,encoding)
        return out
    def __repr__(s):
        return __module__+' instance '+s._path

#________________________________________________
#___ TEST
#________________________________________________
def test():
  stini = """<Server port="80XX" shutdown="SHUTDOWN">
    <Service name="Catalina">
        <Connector port="80YY"/>
        <!-- This is the optional AJP connector -->
        <Connector port="80ZZ" protocol="AJP/1.3"/>
        <Engine name="Catalina" defaultHost="localhost">
            <Host name="localhost" appBase="webapps"/>
        </Engine>
    </Service>
</Server>"""
  p = '===  '

  print (p+"Test of : Module:"+__module__+" version:"+__version__)
  print (p+'With the data :')
  print (stini)
  print (p+'c=xml(st=stini) to instanciates the xml object from a string, use fn=file_name for reading a file')
  c=xml(st=stini)
  print (p+'print (c.Server.port) to gather the attribut port of the Server element.')
  test = (c.Server.port == "80XX")
  print (c.Server.port+': test result :'+str(test))
  print (p+'print (c.Server.Service.Connector.port) to print the attribute port of the element Component .. in fact this is the first element each time')
  test = (c.Server.Service.Connector.port == "80YY")
  print (c.Server.Service.Connector.port+': test result :'+str(test))
  print (p+'print (c.Server.Service.Connector__1.port) to print the same value of the explicit known second element (1) of the filtered element list.')
  test = (c.Server.Service.Connector__1.port == "80ZZ")
  print (c.Server.Service.Connector__1.port+': test result :'+str(test))
  print (p+'For attributes some dictionnary standard functions are available: keys, values, items, has_key, but not itervalues, iterkeys, iteritems or update.')
  print (p+'example: k=c.Server.Service.Engine; print (k.keys(), k.values(), k.items(), k.has_key("port") returns: ')
  k=c.Server.Service.Engine; print (k.keys(), k.values(), k.items(), k.has_key("port"))
  
  print (p+'Additionaly the attribute can be accessed as dictionnary : c.Server.port = c.Server["port"] for reading or update purposes ('+str((c.Server['port'] == c.Server.port) == True)+')')
  c.Server["port1"] = c.Server.port
  result = (c.Server.port1  == c.Server["port"])
  print (p+'The test  c.Server["port1"] = c.Server.port then result = (c.Server.port1  == c.Server["port"]) returns:'+str(result))
  print (p+'We can change the value of an existing attribute: c.Server.port = 8080    Note: all python values are passed by str()')
  c.Server.port = 8080
  print (p+'as well as creates a new attribute: c.Server.Service.Component__1.NewAtt = "coucou"')
  c.Server.Service.Connector__1.NewAtt = "coucou"
  print (p+'or delete one with del(c.Server.shutdown), note: if not exists, no error or del(c.Server["port1"]) note: if not exist the exception NotFoundErr is raised ')
  del c.Server.shutdown

  print (p+'for f in c.Server.Service.Connector__s: print (f.port) ...__s can be used to return the list of sub-elements filtered by name as a list of xml nodes.')
  for f in c.Server.Service.Connector__s: print (f.port)

  print (p+'The following equation is True with a=c.Server.Service: a.Connector == a.Connector__0 == a.Connector__s[0] and in particular here == a[0]') 
  print (p+'for f in s.Server.Service: print ("   "+f._dom.nodeName+":"+f._dom.nodeTyp") can be used to access all sub elements of the Service Element')
  print (p+'This exemple demonstrate in addition that it is still possible to access dom definition as known with the minidom interfaces.')
  for f in c.Server.Service: print ("    "+str(f._dom.nodeName)+":"+str(f._dom.nodeType))
  print (p+'All sub-elements are seen as list elements, same interfaces than for lists are availables')
  print (p+'Slice : print (c.Server.Service[1:-1])')
  print (c.Server.Service[1:-1])
  print (p+'We may print the XML whenever we want with : print(c)')
  print(c)
  print (p+'Or eventually any sub part of this XML : print(c.Server.Service[1]) or str(c.Server.Service[1]) here this is the comment (including CR at the end).')
  test = (str(c.Server.Service[1]) == "<!-- This is the optional AJP connector -->\n")
  print (str(c.Server.Service[1])+': test result :'+str(test))
  
  test = ((len(c.Server.Service) == 4))
  print (p+'For counting sub-elements in an element : print(len(c.Server.Service)) : test result 4 ?:'+str(test))

  print (p+'c.save() save the current xml into a file, s._fn by default except if s._fn is None so then create the file /tmp/xmljv_default_output_file.xml')
  c.save()
  print (p+'The content file is :')
  print (open('/tmp/xmljv_default_output_file.xml').read())
  return c

#________________________________________________
#___ MAIN 
#________________________________________________
if __name__ == '__main__':
  print ("Module "+__module__+" version:"+__version__)
  print ("--------------------------------------------------------------------------")
  print ("Ce Module n'est pas destine a l'execution, il represente une bibliotheques")
  print (" de classes ou de fonctions a utiliser ... voici un exemple")
  print ("--------------------------------------------------------------------------")
  t=test() 

 
