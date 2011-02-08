# -*- coding: utf-8 -*-


model_registry = dict()

def register(model_class, resource_class=None):
    # every model can have just one resource
    # however, a resource may be used for several models
    if resource_class is None:
        from crud.models import Resource
        resource_class = Resource
    model_registry[model_class] = resource_class

def get_registered_types():
    return model_registry.keys()

def get_resource_for_model(model_class):
    try:
        return model_registry[model_class]
    except KeyError:
        # It's not necessary to register each class with crud
        # - those which are not registered will fall back to
        # the generic Resource
        from crud.models import Resource
        return Resource
        # A more meaningful error message
        #raise KeyError("%s has not been registered with crud" % model_class)


class resource(object):
    """
    A decorator which syntax-sugares registering:
    
    @crud.resource(models.Client)
    class ClientResource(crud.Resource):
        ...
        
    """
    def __init__(self, model):
        self.model = model

    def __call__(self, cls):
        register(self.model, cls)
        return cls
