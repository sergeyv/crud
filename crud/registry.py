# -*- coding: utf-8 -*-

##########################################
#     This file forms part of CRUD
#     Copyright: refer to COPYRIGHT.txt
#     License: refer to LICENSE.txt
##########################################

from crud.models import Resource


resource_registries = {}

class ResourceRegistry(object):

    resources = None
    app_name = None
    default_resource = None

    def __init__(self, app_name, default_resource=Resource):
        self.app_name = app_name
        self.resources = {}
        self.default_resource = default_resource

        if app_name in resource_registries:
            raise ValueError("Resource registry %s already exists" % app_name)
        resource_registries[app_name] = self


    def add(self, model_class):

        def decorator(resource_class):
            self.register(model_class, resource_class)
            return resource_class

        return decorator

    def register(self, model_class, resource_class=None):
        # every model can have just one resource
        # however, a resource may be used for several models
        if resource_class is None:
            resource_class = Resource

        self.resources[model_class] = resource_class

    def get_registered_types(self):
        return self.resources.keys()

    def get_resource_for_model(self, model_class):
        try:
            return self.resources[model_class]
        except KeyError:
            # It's not necessary to register each class with crud
            # - those which are not registered will fall back to
            # the generic Resource
            from crud.models import Resource
            return Resource

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
    A decorator which syntax-sugares registering::

        @crud.resource(models.Client)
        class ClientResource(crud.Resource):
            ...

    """
    def __init__(self, model):
        self.model = model

    def __call__(self, cls):
        default_resource_registry.register(self.model, cls)
        return cls
