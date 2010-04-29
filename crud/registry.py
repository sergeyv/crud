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
        # A more meaningful error message
        raise KeyError("%s has not been registered with crud" % model_class)
