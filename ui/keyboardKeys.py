"""
Common module for handling keyboard key events
across different operating systems.
"""
import os
if os.name=='nt':
    from ._windowsKeyboardKeys import sendKeyboardKey,sendKeyboardKeys # noqa: E501,F401 # pylint: disable=wrong-import-position # type: ignore
else:
    from ._unixKeyboardKeys import sendKeyboardKey,sendKeyboardKeys # noqa: E501,F401 # pylint: disable=wrong-import-position # type: ignore
