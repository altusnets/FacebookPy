# flake8: noqa

from .facebookpy import FacebookPy
from .facebookpy import smart_run
from .settings import Settings
from .social_commons.file_manager import set_workspace
from .social_commons.file_manager import get_workspace
from .social_commons import *

# __variables__ with double-quoted values will be available in setup.py
__version__ = "0.1.3"

