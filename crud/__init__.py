#
from registry import register
from registry import get_registered_types
from models import get_root
from models import crud_init

from models import ISection, IModel
from models import Section, ModelProxy


class proxy_for(object):
    
    def __init__(self, model):
        self.model = model

    def __call__(self, cls):
        register(self.model, cls)
        return cls
