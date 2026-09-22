"""
Convert anything to a ui window
"""
import typing
if typing.TYPE_CHECKING:
    from k_runner.processes import ProcessCompatible
    from .component import UiComponent
    from .windowHandleType import WindowHandleType


class ClassWithhwnd(typing.Protocol):
    """
    Any class that contains a compatible hWnd member
    """
    hwnd:"WindowHandleType"
class ClassWithhWnd(typing.Protocol):
    """
    Any class that contains a compatible hWnd member
    """
    hWnd:int


UiComponentCompatible=typing.Union["WindowHandleType",
    "UiComponent",ClassWithhwnd,ClassWithhWnd,"ProcessCompatible"]
UIComponentCompatible=UiComponentCompatible

def asUiComponent(comp:UIComponentCompatible)->"UiComponent":
    """
    Always return a Process
    """
    from .component import UiComponent
    if not isinstance(comp,UiComponent):
        if isinstance(comp,int):
            comp=UiComponent(comp)
        elif hasattr(comp,'hwnd'):
            comp=typing.cast(ClassWithhwnd,comp)
            comp=asUiComponent(comp.hwnd)
        elif hasattr(comp,'hWnd'):
            comp=typing.cast(ClassWithhWnd,comp)
            comp=asUiComponent(comp.hWnd)
        else:
            from .find import pidToHwnd
            comp=typing.cast("ProcessCompatible",comp)
            comp=UiComponent(pidToHwnd(comp)) # type: ignore
    return comp
asComponent=asUiComponent
asUiControl=asUiComponent
asControl=asUiComponent
asUIComponent=asUiComponent
asUIControl=asUiComponent
