# -*- coding: utf-8 -*-


model_registry = dict()

def register(model_class, proxy_class=None):
    # every model can have just one proxy
    # however, a proxy may be used for several models
    if proxy_class is None:
        from crud.models import ModelProxy
        proxy_class = ModelProxy
    model_registry[model_class] = proxy_class

def get_registered_types():
    return model_registry.keys()

def get_proxy_for_model(model_class):
    try:
        return model_registry[model_class]
    except KeyError:
        # It's not necessary to register each class with crud
        # - those which are not registered will fall back to
        # the generic ModelProxy
        from crud.models import ModelProxy
        return ModelProxy
        # A more meaningful error message
        #raise KeyError("%s has not been registered with crud" % model_class)


class proxy_for(object):
    """
    A decorator which syntax-sugares registering:
    
    @crud.proxy_for(models.Client)
    class ClientProxy(crud.ModelProxy):
        ...
        
    """
    def __init__(self, model):
        self.model = model

    def __call__(self, cls):
        register(self.model, cls)
        return cls
