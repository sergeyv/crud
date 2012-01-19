# -*- coding: utf-8 -*-

##########################################
#     This file forms part of CRUD
#     Copyright: refer to COPYRIGHT.txt
#     License: refer to LICENSE.txt
##########################################

from zope.interface import Interface
from zope.interface import implements
# from zope.interface import providedBy

# from webob.exc import HTTPNotFound
from pyramid.url import resource_url
from pyramid.traversal import find_interface
from pyramid.location import lineage

# from pyramid.interfaces import IView
# from pyramid.interfaces import IRequest
# from pyramid.threadlocal import get_current_registry

from sqlalchemy import orm



from crud.forms.fa import FormAlchemyFormFactory

#from sqlalchemy.sql.expression import desc, asc

DBSession = None


class ITraversable(Interface):
    """ """


class IResource(ITraversable):
    """ """


class ICollection(ITraversable):
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
    # IDs are required to be ints - we may think what to do
    # with this limitation later
    q = q.filter_by(id=int(id))
    result = q.first()
    return result


class Traversable(object):
    """
    A base class which implements stuff needed
    for 'traversability'.
    """
    implements(ITraversable)

    subsections = {}
    subitems_source = None
    filter_condition = None


    order_by = None
    """
    A subclass may define an order_by attribute which will be used to order subitems
    The setting can be overridden per-request using the order_by parameter of get_items method
    order_by is a string in format "name;-price;+num_orders" - where a minus results in descending sorting
    """

    show_in_breadcrumbs = True


    resource_registry = None

    def find_resource_registry(self):
        from crud.registry import get_resource_registry_by_name

        if self.resource_registry is not None:
            if isinstance(self.resource_registry, basestring):
                return get_resource_registry_by_name(self.resource_registry)
            return self.resource_registry

        if (self.__parent__ is not None) and hasattr(self.__parent__, 'find_resource_registry'):
            return self.__parent__.find_resource_registry()

        return get_resource_registry_by_name('default')


    def item_url(self, request, view_method=None):
        if view_method:
            return resource_url(self, request, view_method)
        else:
            return resource_url(self, request)

    def parent_url(self, request):
        return resource_url(self.__parent__, request)

    def child_url(self, request, *args):
        # args contain Resources, not real objects
        str_args = []
        for arg in args:
            if IResource.providedBy(arg):
                ### TODO: Do some fancy sluggification here
                arg = str(arg.model.id)
            else:
                arg = str(arg)
            str_args.append(arg)

        return resource_url(self, request, *str_args)

    def __getitem__(self, name):
        """
        This method is crucial to make an object traversable by Pyramid.

        Firstly, it checks if we have a view with the name 'name' registered.
        Secondly, we look up our subsections.
        Lastly, if subitems_source is set, we look up subitems.
        """

        # 1. check if it's our own view
        #registry = get_current_registry()
        #adapters = registry.adapters
        #context_iface = providedBy(self)
        #request_iface = IRequest

        #view_callable = adapters.lookup(
            #(request_iface, context_iface),
            #IView, name=name, default=None)

        #if view_callable is not None:
            #raise KeyError

        ### I've got no idea what makes it a tuple but it happens
        ### This is a quick and dirty fix
        if type(self.subsections) == tuple:
            self.subsections = self.subsections[0]

        # 2. check if it's our subsection
        s = self.subsections.get(name, None)
        if s is not None:
            return self.create_child_subsection(s, name)


        # If it's an int then we suppose it's a subitem
        # if it's not we let Pyramid to look up views
        # and stuff
        try:
            int_name = int(name)
        except ValueError:
            raise KeyError("ID should be an int")

        # 3. look up subitems
        if isinstance(self.subitems_source, str):
            parent_model_resource = find_interface(self, IResource)
            # Some RDBMSes are not happy when we pass a string where
            # it expects a number. And id should be a number.
            model = get_related_by_id(parent_model_resource.model, int_name, self.subitems_source)
        else:
            if self.subitems_source is None:
                raise KeyError("subitems_source is not set")


            model = DBSession.query(self.subitems_source)\
                .filter(self.subitems_source.id == name).first()


        if model is None:
            raise KeyError
        return self.wrap_child(model=model, name=name)

    def get_subsections(self):

        ### I've got no idea what makes it a tuple but it happens
        ### This is a quick and dirty fix
        if type(self.subsections) == tuple:
            self.subsections = self.subsections[0]

        subs = []
        for (n, s) in self.subsections.items():
            subs.append(self.create_child_subsection(s, n))
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
        model = find_interface(self, IResource)
        return model

    def parent_section(self):
        section = find_interface(self, ICollection)
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

        ### BUG BUG BUG: This lousy test only works if the relation is defined with
        ### strings: attr = relationship('Someclass') and it appear to fail if
        ### the actual class is used: attr = relationship(Someclass)
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

    def create_subitem(self, params=None, request=None, wrap=False):
        """
        Creates a new subitem and sets its FK to its
        parent model's PK (if any)

        Also sets the new object properties to the initial values passed
        in params (which is a dict)
        """
        if isinstance(self.subitems_source, str):
            parent_wrapper = self.parent_model()
            parent_instance = parent_wrapper.model
            relation_attr = getattr(parent_instance.__class__, self.subitems_source)
            #related_class = relation_attr.property.argument()
            related_class = self.get_class_from_relation(relation_attr)
            child_instance = related_class()

            # Check if the property is a vector (one-to-many) or a scalar (one-to-one) built using uselist=False in the relation
            mapper = orm.class_mapper(parent_instance.__class__)
            prop = mapper.get_property(self.subitems_source)


            if prop.uselist:
                # it's a list, so we append our item to the list
                collection = getattr(parent_instance, self.subitems_source)
                collection.append(child_instance)
            else:
                # this is a one-to-one relation, so we assign the object to the
                # attribute
                setattr(parent_instance, self.subitems_source, child_instance)

            obj = child_instance
        else:
            # subitems_source is a class -
            # - just create an instance and return it
            # TODO: figure out how to get FK name in this case
            obj = self.subitems_source()


        resource = self.wrap_child(model=obj, name=str(obj.id))

        # AutoFillDropdown requires some changes to the serializer
        # so the latter does a session flush before serializing sequences
        # to load subobjects which were just linked to our item
        # Example:
        #     item.client_id =  123
        #     ... need to flush the session here so item.client is loaded
        #     item.client.name = "Client One"
        # - for this to work we need to add the object to the session first
        # (well, that's because we're using object_session)
        DBSession.add(obj)

        if params is not None:
            resource.deserialize(params, request)

        DBSession.flush()

        if hasattr(resource, "after_item_created"):
            resource.after_item_created(request)

        if wrap:
            return resource

        return resource.model

    def create_transient_subitem(self):
        """
        Just like create_subitem only makes sure the new item is
        not added to session and there are no other persistent side-effects,
        so the item can be safely discarded after we no longer need it
        """
        if isinstance(self.subitems_source, str):
            parent_wrapper = self.parent_model()
            parent_instance = parent_wrapper.model
            relation_attr = getattr(parent_instance.__class__, self.subitems_source)
            related_class = self.get_class_from_relation(relation_attr)
            return related_class()
        else:
            # subitems_source is a class -
            # - just create an instance and return it
            return  self.subitems_source()


    def delete_subitems(self, ids, request):
        """
        Deletes subitems which ids match the list of ids

        for a scalar relation the calling code may pass ids = None
        """

        if ids is not None:
            if len(ids):
                cls = self.get_subitems_class()

                ## TODO: Should we not try to over-optimize and just
                ## call resource.delete_item() instead of attemptimg to
                ## delete everything with a single query? Would this be
                ## better in terms of less surprises when overriding delete_item
                ## method, for example?
                qry = self.get_items_query()
                qry = qry.filter(cls.id.in_(ids))

                # Call the before_item_deleted hook for each item
                for item in qry.all():
                    resource = self.wrap_child(item, name=item.id)
                    resource.delete_item(request)

                    #if hasattr(resource, "before_item_deleted"):
                    #    resource.before_item_deleted(request)

                #qry.delete(synchronize_session=False) # we may have some stale objects in the session with synchronize_session=False, but do we really care? If we do, may change this to "fetch"
        else:
            parent_wrapper = self.parent_model()
            parent_instance = parent_wrapper.model

            # Check if the property is a vector (one-to-many) or a scalar (one-to-one) built using uselist=False in the relation
            mapper = orm.class_mapper(parent_instance.__class__)
            prop = mapper.get_property(self.subitems_source)

            if prop.uselist:
                # it's a list, we can't delete a subitem if no ids were passed
                raise KeyError("%s.%s is not a scalar attribute, need to provide a list of ids to delete subitems" % (parent_instance.__class__.__name__, self.subitems_source))
            else:
                # this is a one-to-one relation (or probably the 'one' end of one-to-meny relation?) so we need to delete the item itself
                item = getattr(parent_instance, self.subitems_source)

                resource = self.wrap_child(item, name=item.id)
                resource.delete_item(request)



    def create_child_subsection(self, origin, name):
        """
        returns a copy of the section
        inserted in the 'traversal context'
        """

        if isinstance(origin, Collection):
            # Finally, it can be an instance of a collection class
            # in which case it's a "child" collection - i.e. using parent's
            # relationship attribute as a source of subitems -
            # "all e-mail addresses" of a particular" user etc.
            section = origin.__class__(title=origin.title,
                subitems_source=origin.subitems_source,
                subsections=origin.subsections,
                order_by=origin.order_by)

            ### TODO: This approach is not very nice because we have to copy
            ### all settings to the new object (which is getting discarded anyway)
            ### use some sort of resource objects which refer to the original
            ### (and immutable) section?
            section.show_in_breadcrumbs = origin.show_in_breadcrumbs

        elif issubclass(origin, Resource):
            # We can have a resource to have another Resource as a direct child
            # without intermediate collection, in case the child is a scalar
            # attribute of the parent (User has a single Address subobject)
            # in which case we can reach the address by traversing to .../users/123/address
            # For this, we need to specify a Resource sublass as the value in subsections:
            #     subsections = {
            #        'address': crud.Resource
            #     }
            # Note that the class we specify there is not really used, wrap_child uses
            # whatever Resource is registered for that model. Kinda clumsy.

            item = getattr(self.model, name)
            return self.wrap_child(item, name)
        else:  # issubclass(origin, Collection): - this breaks subobjects
            # Otherwise, we suppose it's a "global" collection, i.e. not based
            # on an attribute of the parent but containing all the child items
            # instead. Usually used for root collections
            # Also it's used by non-SA-based subobjects, so we just instantiate it
            section = origin()


        section.__name__ = name
        section.__parent__ = self

        return section

    def get_items_query(self, order_by=None, filter_condition=None):
        """
        Returns the query which can be further modified
        """

        related_class = self.get_subitems_class()
        if isinstance(self.subitems_source, str):
            parent_model_resource = find_interface(self, IResource)
            parent_class = parent_model_resource.model
            q = DBSession.query(related_class)
            q = q.with_parent(parent_class, self.subitems_source)
        else:
            q = DBSession.query(related_class)


        # A descendant class can define a class variable 'filter_condition'
        # which defines an additional filter condition
        if self.filter_condition is not None:
            q = q.filter(self.filter_condition)

        # We can also pass a condition to the method on a per-call basis
        if filter_condition is not None:
            q = q.filter(filter_condition)

        # Ordering support: we can override order_by on a per-call basis
        if not order_by:
            order_by = self.order_by

        if order_by is not None:
            q = self._build_order_by_clause(q, related_class, order_by)
        return q


    def _build_order_by_clause(self, query_obj, item_class, order_by_str):
        """
        Parses a string in format "name;-price;+num_orders" and builds an
        order_by clause for a query. Returns the modified query
        """

        if not isinstance(item_class, type):
            raise AttributeError("item_class should be a type")
        fields = []
        for obs in order_by_str.split(';'):
            obs = obs.strip()
            if not obs:
                continue
            need_desc = (obs[0] == '-')
            need_asc = (obs[0] == '+')

            parts = obs.lstrip('+-').split('.')
            relations = parts[:-1]
            attribute_name = parts[-1]
            current_class = item_class
            for rel_name in relations:
                relation = getattr(current_class, rel_name)
                if relation is None:
                    raise AttributeError("WARNING: class %s has no relation %s" % (current_class, rel_name))

                current_class = self.get_class_from_relation(relation)
                if not isinstance(current_class, type):
                    current_class = current_class.__class__
                ## outerjoin returns all items even if the related field is NULL
                query_obj = query_obj.outerjoin(relation)

            field = getattr(current_class, attribute_name)

            if field is None:
                raise AttributeError("Class %s has no attribute %s" % (current_class, attribute_name))

            if not isinstance(field.impl.parent_token, orm.properties.ColumnProperty):
                raise AttributeError("You're trying to order by '%s', which is not a proper column (a relationship maybe?)" % attribute_name)

            if need_desc:
                field = field.desc()
            elif need_asc:
                field = field.asc()
            fields.append(field)


        if fields:
            for f in reversed(fields):
                query_obj = query_obj.order_by(f)

        return query_obj



    def get_items(self, order_by=None, wrap=True, filter_condition=None):
        """
        Returns all subitems of the Traversable

        ``order_by`` - the name of the field to order the result by
        ``wrap`` - whether to wrap the result in Resources or return raw SA objects
        TODO: Add descending sorting and possibly other filtering
        """

        if self.subitems_source is None:
            return []

        q = self.get_items_query(order_by, filter_condition=filter_condition)

        result = q.all()

        ### wrap them in the location-aware resource
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
                    'url': url,
                    'title': item.title,
                    'obj': item,
                })
            url = url.rpartition('/')[0]
        crumbs.reverse()
        return crumbs

    def wrap_child(self, model, name):
        """
        Wrap a model in a correct subsclass of Resource
        and return it as a subitem
        """
        registry = self.find_resource_registry()
        resource_class = registry.get_resource_for_model(model.__class__)
        return resource_class(name=name, parent=self, model=model)


class Resource(Traversable):
    """
    A Resource represents an "item" wrapped around an SQLAlchemy model
    instance. Resource objects are created dynamically during URL traversal,
    i.e. when traversing a URL /users/3, "users" would usually be a Collection,
    and "3" would create a Resource with its `model` attribute set to an instance
    of SQLAlchemy-mapped User class with id=3

    Resources can behave as "folderish" types:

    - if `subitems_source` property is set, a Resource can directly contain other
      items which are fetched from a model's relationship property. Say, if we have
      a Folder model with `children` property, then we could construct a URL in form `/folders/123/234/345`

    - `subsections` property defines a 'subfolder' which contains items fetched
      from an SA relation or directly from an SA-mapped class::

        @crud.resource(models.Group)
        class GroupResource(crud.Resource):
            subsections = {
                'users' : crud.Collection('Users', 'users'),
                'roles' : crud.Collection('All Roles', models.UserRole)
            }



    """
    implements(IResource)


    form_factory = FormAlchemyFormFactory()
    """
    Set FA form factory as the default (as this is the only one
    functional factory at the moment anyway)
    """


    def __init__(self, name, parent, model,\
        subitems_source=None, subsections=None, order_by=None):
        self.__name__ = name
        self.__parent__ = parent
        self.model = model

        if subitems_source is not None:
            self.subitems_source = subitems_source

        if subsections is not None:
            self.subsections = subsections

        if order_by is not None:
            self.order_by = order_by


    def __unicode__(self):
        return unicode(self.model)

    @property
    def title(self):
        """
        Returns string representation of the model. Used in crud's UI
        """

        return str(self.model)


    def delete_item(self, request=None):
        """
        Deletes the model from the database

        The callback can prevent the deletion by returning "ABORT"
        (is there a better way?)
        """

        if hasattr(self, "before_item_deleted"):
            callback_result = self.before_item_deleted(request)
            if callback_result == "ABORT":
                return

        DBSession.delete(self.model)


    def update(self, params, request):
        self.deserialize(params, request)

        #Flush session so changes have been applied
        # before we call the after context hook
        DBSession.flush()

        if hasattr(self, "after_item_updated"):
            self.after_item_updated(request)

    def deserialize(self, params, request):
        """
        A basic method which accepts a dictionary with data
        and applies it to the model.

        There's currently no validation or schema checks
        """

        # TODO: Add validation here
        item = self.model

        for (k, v) in params.items():
            if v:  # Do not set empty fields
                setattr(item, k, v)


class Collection(Traversable):
    """
    A `Collection` is a virtual "folder" which is defined in code and not mapped
    to an SQLAlchemy model. It can contain other Collections or Resources.

    A Collection can be purely 'virtual' and not related to any SQL data::


        class AboutCollection(crud.Collection):
            pass

        class RootCollection(crud.Collection):

            subsections = {
                'about' : AboutCollection,
            }

    This code will create a "root collection" which can be passed to Pyramid's configurator::


        def root_factory(request):
            return RootCollection(request)

        config = Configurator(
            root_factory=root_factory
            ...
            )

    We also need to tell crud which SQLAlchemy session to use::

        import crud
        crud.crud_init(DBSession)

    After this, the `/` url will be mapped to the default view attached the RootCollection and `/about` will invoke the view attached to the AboutCollection

    Also, we can use a Collection as a folder which contains all items of some SA-mapped class::

         class RootCollection(crud.Collection):

            subsections = {
                'members' : crud.Collection("Our beloved members", models.Member),
            }

    This declaration will create a 'members' folder which contains `Resource` objects wrapped around `Member` SA models. They will be accessible as `/members/123` etc., where `123` is the ID of corresponding Member object.

    Apart from that, we can map a Collection to a relationship attribute of an SA model, so the Collection will contain "subitems" of a particular "item". Continuing the previous example::

        @crud.resource(models.Member)
        class MemberResource(crud.Resource):

            subsections = {
                'photos' : crud.Collection("Member's photos", "photos")
            }

    Here we're telling `crud` to create a Collection which contains photos belonging to a particular member, using `photos` relationship property defined on the Member class. This will result in the following URLs:

        - `/members/123` will display a Member

        - `/members/123/photos` will display a list of photos belonging to the Member #123

        - `/members/123/photos/34` will display a Photo with id=32 belonging to the Member #123


    """

    implements(ICollection)


    def __init__(self, title=None, subitems_source=None, \
        subsections=None, order_by=None):
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

        if order_by is not None:
            self.order_by = order_by


    def _get_title(self):
        return getattr(self, '_title', self.__name__)

    def _set_title(self, title):
        self._title = title

    title = property(_get_title, _set_title)


    def __repr__(self):
        return "Collection %s (%s)" % (self.title, self.subitems_source)




def crud_init(session):
    """
    Initializes crud by setting the SA session
    """
    global DBSession
    DBSession = session

