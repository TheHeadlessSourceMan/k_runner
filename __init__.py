"""
This module is for smartly running system commands
and processing their io streams.
"""
from .kRunnerTools import *
from .pyErrRun import *
from .runPythonFile import *
from .runSomething import *
from .cmdline import *

from .ui import *
import .ui as uifiddle # legacy support
import .ui as windowManipulator # legacy support

from .processes import *
import .processes as processPlayset # legacy support
import .processes as processManipulator # legacy support
import .processes as possiblyRunningApplication # legacy support
