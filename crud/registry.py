# -*- coding: utf-8 -*-

##########################################
#     This file forms part of CRUD
#     Copyright: refer to COPYRIGHT.txt
#     License: refer to LICENSE.txt
##########################################

from crud.models import Resource


resource_registries = {}

class ResourceRegistry(object):
    """
    a ResourceRegistry maps Resources to their models. A default registry
    is created by crud so most applications can use the global `register` function
    defined here:

        @crud.register(models.Client)
        class ClientResource(crud.Resource):
            ....

    However, a global registry means we only can have one mapping interpreter-wide,
    i.e. even for several WSGI application running in the same process - so if we
    need to have different mapping of the same models, the applications can define
    and use their own local registries:

        registry = ResourceRegistry("myapp")
        @registry.add(models.Client)
        class ClientResource(crud.Resource):
            ...

    """

    resources = None
    app_name = None
    default_resource = None

    def __init__(self, app_name, default_resource=Resource):
        """
        Creates a ResourceRegistry.

        `app_name` is a unique name of the registry (the default global registry
        is called 'default')

        default_resource is the resource class to use for models which are
        not explicitly registered with crud. If None, an exception will be raised
        when trying to wrap a model
        """
        self.app_name = app_name
        self.resources = {}
        self.default_resource = default_resource

        if app_name in resource_registries:
            raise ValueError("Resource registry %s already exists" % app_name)
        resource_registries[app_name] = self


    def add(self, model_class):
        """
        A decorator which syntax-sugares registering::

            registry = ResourceRegistry("myapp")
            @registry.add(models.Client)
            class ClientResource(crud.Resource):
                ...

        """

        def decorator(resource_class):
            self.register(model_class, resource_class)
            return resource_class

        return decorator

    def register(self, model_class, resource_class=None):
        """
        Register the mapping between a model class and a resource::

            registry = ResourceRegistry("myapp")
            registry.register(models.Client, ClientResource)

        The `resource_class` parameter can be omitten, in which case the default_resource
        specified during the resource creation will be used (however, in this case it's not
        necessary to register the model anyway)
        """
        # every model can have just one resource
        # however, a resource may be used for several models
        if resource_class is None:
            resource_class = self.default_resource

        if model_class in self.resources:
            raise ValueError("Model %s is already registered with resource %s - can't re-register with %s" % (model_class, self.resources[model_class], resource_class))
        self.resources[model_class] = resource_class

    def get_registered_types(self):
        return self.resources.keys()

    def get_resource_for_model(self, model_class):
        try:
            return self.resources[model_class]
        except KeyError:
            # It's not necessary to register each class with crud
            # - those which are not registered will fall back to
            # the default_resource provided during registry creation
            if self.default_resource is None:
                raise AttributeError("Model %s is not registered with registry '%s' and there's no fallback" % (model_class, self.app_name) )
            return self.default_resource

    def get_model_for_resource(self, resource_class):
        for (model_cls, res_cls) in self.resources.items():
            if resource_class == res_cls:
                return model_cls


# Create a default resource registry to support the old behaviour
# TODO: Do we want to remove it eventually?
default_resource_registry = ResourceRegistry('default')

def get_resource_registry_by_name(name):
    return resource_registries[name]


class resource(object):
    """
    A decorator which syntax-sugares registering

    it uses the default registry to support the old behaviour
    """
    def __init__(self, model):
        self.model = model

    def __call__(self, cls):
        default_resource_registry.register(self.model, cls)
        return cls


def register(model_class, resource_class):
    """
    Register a model in the default registry
    """
    default_resource_registry.register(model_class, resource_class)

