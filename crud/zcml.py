## -*- coding: utf-8 -*-

###########################################
##     This file forms part of CRUD
##     Copyright: refer to COPYRIGHT.txt
##     License: refer to LICENSE.txt
###########################################


#from zope.interface import Interface
#from zope.configuration.xmlconfig import include, includeOverrides
#from zope.configuration.fields import GlobalObject
#from zope.schema import BytesLine, TextLine


#class IRegisterDirective(Interface):
    #"""
    #register directive registers an SA model with crud's Resource so that resource is
    #instantiated when, for example, URL traversal is happening
    #"""


    #model = GlobalObject(
        #title=u"Crud model",
        #description=u""" """,
        #required=True,
        #)


    #resource = GlobalObject(
        #title=u"Crud resource",
        #description=u""" """,
        #required=True,
        #)

#def register(_context, model, resource):
    #"""
    #registers an SA model with crud
    #<crud:register model=".models.Client" resource=".proxies.ClientResource" />

    #You can use ZCML or, alternatively, use the @resource decorator (see registry.py)
    #"""
    #import crud
    #crud.register(model, resource)


#class ICollectionDirective(Interface):
    #"""
    #crud directive registers a CRUD section
    #"""

    #title = TextLine(
        #title=u"Title",
        #description=(u""),
        #required=True,
        #)

    #slug = TextLine(
        #title=u"Slug",
        #description=(u""),
        #required=True,
        #)

    #section = GlobalObject(
        #title=u"Crud object",
        #description=u""" """,
        #required=True,
        #)

    #model = GlobalObject(
        #title=u"Crud object",
        #description=u""" """,
        #required=False, # Someitmes we want Collections without any subitems
        #)

#def section(_context, slug, title, section, model=None):
    #""" registers a CRUD section """
    #import crud

    #root = crud.get_root()

    ## Avoid assigning stuff to the class attribute
    #if root is not None:
        #root.__dict__.setdefault('subsections', {})[slug] = section(title, model)
