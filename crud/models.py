# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope.interface import implements

from webob.exc import HTTPNotFound
from repoze.bfg.url import model_url
from repoze.bfg.traversal import find_interface
from repoze.bfg.location import lineage

from sqlalchemy import orm

from crud.registry import get_proxy_for_model

from crud.forms.fa import FormAlchemyFormFactory

DBSession = None

class ITraversable(Interface):
    """ """

class IModel(ITraversable):
    """ """

class ISection(ITraversable):
    """ """


###
### CRUD permissions are: crud.add, crud.edit, crud.view, crud.list, crud.delete
###

def get_related_by_id(obj, id, property_name=None):
    print "GET RELATED BY ID: obj=%s, id=%s, property_name=%s" % (obj,id, property_name)

    import traceback
    traceback.print_stack()

    relation = getattr(obj.__class__, property_name)
    related_class = relation.property.argument()
    print "related class is %s" % related_class
    q = DBSession.query(related_class)
    q = q.with_parent(obj, property_name)
    q = q.filter_by(id=int(id))
    result = q.first()
    return result

class Traversable(object):
    """
    A base class which implements stuff needed
    for 'traversability'
    """
    implements(ITraversable)
    #__name__ = ''
    #__parent__ = None
    subsections = {}
    subitems_source = None
    views = []

    show_in_breadcrumbs = True

    def item_url(self, request, view_method=None):
        print "getting url for %s" % self
        print "    parent is %s" % self.__parent__
        print "    name is %s" % self.__name__
        print "    url is %s" % model_url(self, request)
        if view_method:
            return model_url(self, request, view_method)
        else:
            return model_url(self, request)

    def parent_url(self, request):
        return model_url(self.__parent__, request)

    def child_url(self, request, *args):
        # args contain ModelProxies, not real objects
        str_args = []
        for arg in args:
            if IModel.providedBy(arg):
                ### TODO: Do some fancy sluggification here
                arg = str(arg.model.id)
            else:
                arg = str(arg)
            str_args.append(arg)

        print "self: %s, request:%s, args: %s, str_args: %s" % (self, request, args, str_args)
        return model_url(self, request, *str_args)

    def __getitem__(self, name):

        print "GGG"
        # 1. check if it's our own view
        ## TODO: Try to get a real view using queryMultiAdapter here
        ## get rid of self.views
        if name in self.views:
            raise KeyError

        # 2. check if it's our subsection
        s = self.subsections.get(name, None)
        if s is not None:
            return s.with_parent(self, name)

        # 3. look up subitems
        if isinstance(self.subitems_source, str):
            parent_model_proxy = find_interface(self, IModel)
            model = get_related_by_id(parent_model_proxy.model, name, self.subitems_source)
        else:
            model = DBSession.query(self.subitems_source)\
                .filter(self.subitems_source.id==name).first()
        if model is None:
            raise KeyError
        #proxy_class = get_proxy_for_model(model.__class__)
        #print "Proxy for %s is %s" % (model.__class__, proxy_class)
        #return proxy_class(name=name, parent=self, model=model)
        return self.wrap_child(model=model, name=name)

    def get_subsections(self):
        return [s.with_parent(self,n) for (n,s) in self.subsections.items()]

    def can_have_subitems(self):
        """
        Checks if the model/section can have subitems in principle
        i.e. it has subitems_source set
        """
        return self.subitems_source is not None

    def has_subsections(self):
        return self.subsections and len(self.subsections.items())

    def parent_model(self):
        model = find_interface(self, IModel)
        return model

    def parent_section(self):
        section = find_interface(self, ISection)
        return section

    def get_subitems_class(self):
        if isinstance(self.subitems_source, str):
            parent_model = self.parent_model()
            relation = getattr(parent_model.model.__class__, self.subitems_source)
            #import pdb
            #pdb.set_trace()
            related_class = relation.property.argument()
            return related_class
        else:
            return self.subitems_source

    def create_subitem(self):
        """
        Creates a new subitem and sets its FK to its
        parent model's PK (if any)
        """
        if isinstance(self.subitems_source, str):
            parent_wrapper = self.parent_model()
            parent_instance = parent_wrapper.model
            relation_attr = getattr(parent_instance.__class__, self.subitems_source)
            related_class = relation_attr.property.argument()
            child_instance = related_class()
            #assert False
            ### This works incorrectly for self-referential stuff
            for pair in relation_attr.property.local_remote_pairs:
                parent_attr_name = pair[0].key
                value = getattr(parent_instance, parent_attr_name)
                child_attr_name = pair[1].key
                setattr(child_instance, child_attr_name, value)

            return child_instance
        else:
            # subitems_source is a class -
            # - just create an instance and return it
            # TODO: figure out how to get FK name in this case
            return self.subitems_source()

    def get_items(self):
        if self.subitems_source is None:
            return []
        if isinstance(self.subitems_source, str):
            related_class = self.get_subitems_class()
            parent_model_proxy = find_interface(self, IModel)
            parent_class = parent_model_proxy.model
            print "related class is %s" % related_class
            q = DBSession.query(related_class)
            q = q.with_parent(parent_class, self.subitems_source)
        else:
            q = DBSession.query(self.subitems_source)
        result = q.all()
        # wrap them in the location-aware proxy

        if len(result):
            sample = result[0]
            #proxy_class = get_proxy_for_model(model.__class__)
            #result = [proxy_class(name=str(obj.id), parent=self, model=obj) for obj in result]
            result = [self.wrap_child(model=model, name=str(model.id)) for model in result]

        return result

    def breadcrumbs(self, request):
        """
        returns a list of dicts {url, title, obj}
        """
        url = self.item_url(request)
        parents = lineage(self)
        crumbs = []
        (url, sep, nothing) = url.rpartition('/')
        for item in parents:
            if item.show_in_breadcrumbs:
                crumbs.append({
                    'url' : url,
                    'title' : item.title,
                    'obj' : item,
                })
            url = url.rpartition('/')[0]
        crumbs.reverse()
        return crumbs

    def wrap_child(self, model, name):
        """
        Wrap a model in a correct subsclass of ModelProxy
        and return it as a subitem
        """
        proxy_class = get_proxy_for_model(model.__class__)
        return proxy_class(name=name, parent=self, model=model)

class ModelProxy(Traversable):
    implements(IModel)

    pretty_name = 'Model'

    views = ('add', 'edit', 'save', 'delete', 'save_new')

    # Set FA form factory as the default (as this is the only one
    # functional factory at the moment anyway)

    form_factory = FormAlchemyFormFactory()

    #form_factory = None


    def __init__(self, name, parent, model):
        self.__name__ = name
        self.__parent__ = parent
        self.model = model

    def __repr__(self):
        return self.model.__repr__()

    @property
    def title(self):
        return getattr(self.model, 'title',
                    getattr(self.model, 'name',
                    "%s %s" % (self.pretty_name, self.model.id)))


class Section(Traversable):
    implements(ISection)

    views = ('add','save_new','delete')

    def __init__(self, title, subitems_source=None, subsections = {}):
        self.__name__ = None
        self.__parent__ = None
        self.title = title
        self.subitems_source = subitems_source
        self.subsections = subsections

    def __repr__(self):
        return "Section %s (%s)" % (self.title, self.subitems_source)

    def with_parent(self, parent, name):
        """
        returns a copy of the section
        inserted in the 'traversal context'
        """
        #if self.__parent__ == parent:
        #    self.__name__ = name
        #    return self
        section = self.__class__(title=self.title,
            subitems_source=self.subitems_source,
            subsections = self.subsections )
        section.__name__ = name
        section.__parent__ = parent

        ### TODO: This approach is not very nice because we have to copy
        ### all settings to the new object (which is getting discarded anyway)
        ### use some sort of proxy objects which refer to the original
        ### (and immutable) section?
        section.show_in_breadcrumbs = self.show_in_breadcrumbs
        return section


crud_root = None

def get_root(environ=None):
    print "CRUD_ROOT is %s" % crud_root
    return crud_root


def crud_init( session, root ):
    global DBSession
    DBSession = session

    global crud_root
    crud_root = root


