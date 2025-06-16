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
import k_runner.ui as uifiddle # legacy support
import k_runner.ui as windowManipulator # legacy support

from .processes import *
import k_runner.processes as processPlayset # legacy support
import k_runner.processes as processManipulator # legacy support
import k_runner.processes as possiblyRunningApplication # legacy support
