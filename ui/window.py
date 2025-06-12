"""
A window is a UiItem with the possiblility of having tabs
along with just children
"""
import typing
import os
if os.name=='nt':
    import win32gui
from .component import UiComponent # pylint: disable=wrong-import-position
from .componentGroup import UiGroupWithTabs # noqa: E501 # pylint: disable=wrong-import-position
if typing.TYPE_CHECKING:
    from .asUiComponent import UiComponentCompatible


class UiWindow(UiGroupWithTabs,UiComponent):
    """
    A window is a UiItem with the possiblility of having tabs
    along with just children
    """

    def __init__(self,hWnd:"UiComponentCompatible"):
        UiGroupWithTabs.__init__(self)
        UiComponent.__init__(self,hWnd)

    def bringToFront(self):
        """
        Bring the window to front
        """
        if os.name=='nt':
            win32gui.ShowWindow(self.hWnd,5)
            win32gui.SetForegroundWindow(self.hWnd)
        else:
            raise NotImplementedError()

UIWindow=UiWindow
Window=UiWindow
