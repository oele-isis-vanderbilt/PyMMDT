"""PyMMDT Package.

PyMMDT is a package that focus on multimodal data analytics and 
visualization.

"""

# Adding the path of PyMMDT to PATH
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .data_stream import DataStream
from .process import Process
from .collector import Collector
from .pipe import Pipe
from .session import Session
from .data_source import DataSource, Sensor, Api
from . import tools
