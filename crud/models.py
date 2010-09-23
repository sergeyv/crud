# -*- coding: utf-8 -*-
from zope.interface import Interface
from zope.interface import implements
from zope.interface import providedBy

from webob.exc import HTTPNotFound
from repoze.bfg.url import model_url
from repoze.bfg.traversal import find_interface
from repoze.bfg.location import lineage

from repoze.bfg.interfaces import IView
from repoze.bfg.interfaces import IRequest
from repoze.bfg.threadlocal import get_current_registry

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

    relation = getattr(obj.__class__, property_name)
    #related_class = relation.property.argument()

    arg = relation.property.argument
    ### TODO: This is not a proper test, it's just a coincidence
    ### thet it's callable in one case and not callable in another
    if callable(arg):
        # the relationship is defined on our class
        related_class = arg()
    else:
        # the relationship is defined on the other class,
        # and we have a backref, so arg is a Mapper object
        related_class = arg.class_

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

    show_in_breadcrumbs = True

    def item_url(self, request, view_method=None):
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

        return model_url(self, request, *str_args)

    def __getitem__(self, name):

        # 1. check if it's our own view
        registry = get_current_registry()
        adapters = registry.adapters
        context_iface = providedBy(self)
        request_iface = IRequest

        view_callable = adapters.lookup(
            (request_iface, context_iface),
            IView, name=name, default=None)

        if view_callable is not None:
            raise KeyError


        ### I've got no idea what makes it a tuple but it happens
        ### This is a quick and dirty fix
        if type(self.subsections) == tuple:
            self.subsections = self.subsections[0]

        # 2. check if it's our subsection
        s = self.subsections.get(name, None)
        if s is not None:
            return self.create_child_subsection(s, name)

        # 3. look up subitems
        if isinstance(self.subitems_source, str):
            parent_model_proxy = find_interface(self, IModel)
            model = get_related_by_id(parent_model_proxy.model, name, self.subitems_source)
        else:
            if self.subitems_source is None:
                raise KeyError

            model = DBSession.query(self.subitems_source)\
                .filter(self.subitems_source.id==name).first()
        if model is None:
            raise KeyError
        #proxy_class = get_proxy_for_model(model.__class__)
        return self.wrap_child(model=model, name=name)

    def get_subsections(self):

        ### I've got no idea what makes it a tuple but it happens
        ### This is a quick and dirty fix
        if type(self.subsections) == tuple:
            self.subsections = self.subsections[0]

        for s in self.subsections:
            print s
        subs = []
        for (n,s) in self.subsections.items():
            subs.append(self.create_child_subsection(s,n))
        return subs

    def can_have_subitems(self):
        """
        Checks if the model/section can have subitems in principle
        i.e. it has subitems_source set
        """
        return self.subitems_source is not None

    def has_subsections(self):
        return self.subsections and len(self.subsections.keys())

    def parent_model(self):
        model = find_interface(self, IModel)
        return model

    def parent_section(self):
        section = find_interface(self, ISection)
        return section

    def get_class_from_relation(self, relation):
        """
        Returns class given relation attribute
        """
        ### There are two options - either our class defines a relationship itself or
        ### the relationship is defined in the other class and the attribute is
        ### set by a backref

        arg = relation.property.argument
        ### TODO: This is not a proper test, it's just a coincidence
        ### that it's callable in one case and not callable in another
        if callable(arg):
            # the relationship is defined on our class
            related_class = arg()
        else:
            # the relationship is defined on the other class,
            # and we have a backref, so arg is a Mapper object
            related_class = arg.class_
        return related_class


    def get_subitems_class(self):
        if isinstance(self.subitems_source, str):
            parent_model = self.parent_model()
            relation = getattr(parent_model.model.__class__, self.subitems_source)
            return self.get_class_from_relation(relation)
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
            #related_class = relation_attr.property.argument()
            related_class = self.get_class_from_relation(relation_attr)
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


    def create_child_subsection(self, origin, name):
        """
        returns a copy of the section
        inserted in the 'traversal context'
        """

        if type(origin) == type:
            section = origin()
        else:
            section = origin.__class__(title=origin.title,
                subitems_source=origin.subitems_source,
                subsections = origin.subsections )

            ### TODO: This approach is not very nice because we have to copy
            ### all settings to the new object (which is getting discarded anyway)
            ### use some sort of proxy objects which refer to the original
            ### (and immutable) section?
            section.show_in_breadcrumbs = origin.show_in_breadcrumbs

        section.__name__ = name
        section.__parent__ = self

        return section

    def get_items_query(self, order_by=None):
        """
        Returns the query which can be further modified
        """
        related_class = self.get_subitems_class()
        if isinstance(self.subitems_source, str):
            parent_model_proxy = find_interface(self, IModel)
            parent_class = parent_model_proxy.model
            q = DBSession.query(related_class)
            q = q.with_parent(parent_class, self.subitems_source)
        else:
            q = DBSession.query(related_class)

        if order_by is not None:
            order_by_field = getattr(related_class, order_by)
            q = q.order_by(order_by_field)

        return q


    def get_items(self, order_by=None, wrap=True):
        """
        Returns all subitems of the Traversable
        @param order_by - the name of the field to order the result by
        @param wrap - whether to wrap the result in ModelProxies or return raw SA objects
        TODO: Add descending sorting and possibly other filtering
        """

        if self.subitems_source is None:
            return []

        q = self.get_items_query(order_by)

        result = q.all()

        ### wrap them in the location-aware proxy
        if wrap and len(result):
            result = [self.wrap_child(model=model, name=str(model.id)) for model in result]

        return result

    def get_item(self, id):
        """
        Returns a single item from the collection by its ID
        """
        classobj = self.get_subitems_class()
        q = self.get_items_query()
        result = q.filter(classobj.id == id).one()
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

    # Set FA form factory as the default (as this is the only one
    # functional factory at the moment anyway)

    form_factory = FormAlchemyFormFactory()

    #form_factory = None


    def __init__(self, name, parent, model, subitems_source=None, subsections = None):
        self.__name__ = name
        self.__parent__ = parent
        self.model = model

        if subitems_source is not None:
            self.subitems_source = subitems_source

        if subsections is not None:
            self.subsections = subsections


    def __repr__(self):
        return self.model.__repr__()

    @property
    def title(self):
        return repr(self.model)
        #return getattr(self.model, 'title',
        #            getattr(self.model, 'name',
        #            "%s %s" % (self.pretty_name, self.model.id)))


class Section(Traversable):
    implements(ISection)


    def __init__(self, title=None, subitems_source=None, subsections = None):
        self.__name__ = None
        self.__parent__ = None
        if title is not None:
            self.title = title

        if subitems_source is not None:
            self.subitems_source = subitems_source
        #See http://code.activestate.com/recipes/502206-re-evaluatable-default-argument-expressions/
        # - do not pass lists as a default argument
        if subsections is not None:
            self.subsections = subsections


    def _get_title(self):
        return getattr(self, '_title', self.__name__)

    def _set_title(self, title):
        self._title = title

    title = property(_get_title, _set_title)


    def __repr__(self):
        return "Section %s (%s)" % (self.title, self.subitems_source)


    #def with_parent(self, parent, name):
        #"""
        #returns a copy of the section
        #inserted in the 'traversal context'
        #"""
        ##if self.__parent__ == parent:
        ##    self.__name__ = name
        ##    return self

        #section = self.__class__(title=self.title,
            #subitems_source=self.subitems_source,
            #subsections = self.subsections )
        #section.__name__ = name
        #section.__parent__ = parent

        #### TODO: This approach is not very nice because we have to copy
        #### all settings to the new object (which is getting discarded anyway)
        #### use some sort of proxy objects which refer to the original
        #### (and immutable) section?
        #section.show_in_breadcrumbs = self.show_in_breadcrumbs
        #return section


crud_root = None

def get_root(environ=None):
    return crud_root


def crud_init( session, root ):
    global DBSession
    DBSession = session

    global crud_root
    crud_root = root


