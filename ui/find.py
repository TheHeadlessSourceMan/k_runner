"""
Tools for finding windows
"""
import typing
import os
import re
if os.name=='nt':
    import win32process
    import win32gui
if typing.TYPE_CHECKING:
    from processes.asProcess import ProcessCompatible
from .window import Window # pylint: disable=wrong-import-position


def allTopLevelHwnds()->typing.Iterable[int]:
    """
    Loop through all top level window handles
    """
    hwnds:typing.List[int]=[]
    if os.name=='nt':
        def cb(hwnd:int,hwnds:typing.List[int]):
            hwnds.append(hwnd)
        win32gui.EnumWindows(cb,hwnds)
    else:
        raise NotImplementedError('Need to implement for this os')
    return hwnds


def getTopLevelWindows(
    matching:typing.Union[None,str,typing.Pattern[str]]=None
    )->typing.Generator[Window,None,None]:
    """
    Get all the application windows matching a given pattern
    """
    if matching is not None and isinstance(matching,str):
        matching=re.compile(matching,re.DOTALL)
    children:typing.List[Window]=[]
    def winEnumHandler(hwnd:int,ctx:typing.Any):
        _=ctx
        if win32gui.IsWindowVisible(hwnd):
            title=win32gui.GetWindowText(hwnd).strip()
            if matching is None or matching.match(title):
                children.append(Window(hwnd))
    win32gui.EnumWindows(winEnumHandler,None)
    for c in children:
        yield c


def findWindows(
    title:typing.Union[None,str,typing.Pattern[str]]=None,
    visible:typing.Optional[bool]=None,
    location:typing.Optional[tuple[int,int]]=None,
    recursive:bool=False,
    startingAt:typing.Union[None,int,typing.Iterable[int]]=None,
    caseSensitive:bool=True
    )->typing.Generator[Window,None,None]:
    """
    Find windows given a set of criteria
    """
    tape=[]
    def appendTape(hWndChild:int,_:typing.Any=None):
        tape.append(hWndChild)
    if startingAt is None:
        tape=list(allTopLevelHwnds())
    else:
        if isinstance(startingAt,int):
            startingAt=[startingAt]
        for hWnd in startingAt:
            win32gui.EnumChildWindows(hWnd,appendTape,None)
    if title is not None and isinstance(title,str) and not caseSensitive:
        title=title.lower()
    for hWnd in tape:
        if recursive:
            win32gui.EnumChildWindows(hWnd,appendTape,None)
        if visible is not None:
            if win32gui.IsWindowVisible(hWnd)!=visible:
                continue
        if location is not None:
            bounds=win32gui.GetWindowPlacement(hWnd)
            if location[0]<bounds[0]:
                continue
            if location[0]>bounds[0]+bounds[2]: # type: ignore
                continue
            if location[1]<bounds[1]:
                continue
            if location[1]>bounds[1]+bounds[3]: # type: ignore
                continue
        if title is not None:
            #txt=win32gui.GetWindowText(hWnd).strip()
            txt=str(win32gui.GetWindowTitle(hWnd)).strip() # type: ignore
            if isinstance(title,str):
                if txt.lower().find(title)<0:
                    continue
            elif title.match(txt) is None:
                continue
        yield Window(hWnd)


def pidToHwnds(pid:"ProcessCompatible")->typing.Iterable[int]:
    """
    Get all top-level window handles for a process id
    """
    if not isinstance(pid,int):
        from processes.asProcess import asProcess
        pid=int(asProcess(pid))
    if os.name=='nt':
        for hWnd in allTopLevelHwnds():
            _,windowPid=win32process.GetWindowThreadProcessId(hWnd)
            if windowPid==pid:
                yield hWnd
    else:
        raise NotImplementedError('Need to implement for this os')


def pidToHwnd(pid:"ProcessCompatible")->int:
    """
    Get the main window handle for a process id

    If the pid has no associated windows, could throw IndexError
    """
    for hWnd in pidToHwnds(pid):
        return hWnd
    raise IndexError()
