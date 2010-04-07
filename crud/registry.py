
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
    print "class is %s" % model_class
    print "registry is %s" % (model_registry,)
    return model_registry[model_class]
