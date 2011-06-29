##########################################
#     This file forms part of CRUD
#     Copyright: refer to COPYRIGHT.txt
#     License: refer to LICENSE.txt
##########################################


# Add an alias to keep FormAlchemy happy
# TODO: This ultimately needs to be fixed in FormAlchemy
# or we need to get rid of it
import sys
import sqlalchemy.exc as exceptions
sys.modules['sqlalchemy.exceptions'] = exceptions

from registry import register, resource, get_registered_types
from models import get_root
from models import crud_init

from models import ICollection, IResource
from models import Collection, Resource

