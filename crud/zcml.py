# -*- coding: utf-8 -*-

from zope.interface import Interface
from zope.configuration.xmlconfig import include, includeOverrides
from zope.configuration.fields import GlobalObject
from zope.schema import BytesLine, TextLine


class IRegisterDirective(Interface):
    """
    register directive registers an SA model with crud's ModelProxy so that proxy is
    instantiated when, for example, URL traversal is happening
    """


    model = GlobalObject(
        title=u"Crud model",
        description=u""" """,
        required=True,
        )


    proxy = GlobalObject(
        title=u"Crud proxy",
        description=u""" """,
        required=True,
        )

def register(_context, model, proxy):
    """ 
    registers an SA model with crud 
    <crud:register model=".models.Client" proxy=".proxies.ClientProxy" />
    
    You can use ZCML or, alternatively, use the proxy_for decorator (see registry.py)
    """
    import crud
    crud.register(model, proxy)


class ISectionDirective(Interface):
    """
    crud directive registers a CRUD section
    """

    title = TextLine(
        title=u"Title",
        description=(u""),
        required=True,
        )

    slug = TextLine(
        title=u"Slug",
        description=(u""),
        required=True,
        )

    section = GlobalObject(
        title=u"Crud object",
        description=u""" """,
        required=True,
        )

    model = GlobalObject(
        title=u"Crud object",
        description=u""" """,
        required=False, # Someitmes we want Sections without any subitems
        )

def section(_context, slug, title, section, model=None):
    """ registers a CRUD section """
    import crud

    root = crud.get_root()
    print "Registering section %s (%s)" % (slug, title)

    # Avoid assigning stuff to the class attribute
    if root is not None:
        root.__dict__.setdefault('subsections', {})[slug] = section(title, model)
