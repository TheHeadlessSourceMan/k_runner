#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This program creates a detached desktop that can be used
as a canvas for remote rendering.
"""
import typing
from win32gui import ( # type: ignore
    BringWindowToTop,
    CreateCompatibleBitmap,
    CreateCompatibleDC,
    DeleteDC,
    DeleteObject,
    GetWindowDC,
    GetWindowRect,
    SelectObject)
from win32service import (
    CreateDesktop,OpenDesktop,PyHDESK, # type: ignore
    GetProcessWindowStation,PyHWINSTA) # type: ignore

class _DesktopManager:
    """
    Manage virtual desktops
    """
    _hwndsta:PyHWINSTA=GetProcessWindowStation()

    @property
    def desktopNames(self)->typing.Iterable[str]:
        """
        List all of the desktop names
        """
        return self._hwndsta.EnumDesktops()

    def create(self,
        desktopName:str,
        deleteCreatedOnExit:bool=True
        )->"Desktop":
        """
        Create a desktop
        """
        return Desktop(
            desktopName,
            True,
            True,
            deleteCreatedOnExit)

    def getDesktop(self,
        desktopName:str,
        alwaysCreateNew:bool=False,
        createIfMissing:bool=True,
        deleteCreatedOnExit:bool=True
        )->"Desktop":
        """
        Get a desktop
        """
        return Desktop(
            desktopName,
            alwaysCreateNew,
            createIfMissing,
            deleteCreatedOnExit)

    def __call__(self)->"_DesktopManager":
        return self

    def __del__(self):
        self._hwndsta.Detach()

DesktopManager=_DesktopManager()
desktopManager=DesktopManager
desktops=DesktopManager
Desktops=desktops


class UiDesktop:
    """
    This either references a virtual desktop or creates
    a new one.

    See also:
        https://msdn.microsoft.com/en-us/library/windows/desktop/ms682127(v=vs.85).aspx
    """

    def __init__(self,
        desktopName:str,
        alwaysCreateNew:bool=False,
        createIfMissing:bool=True,
        deleteCreatedOnExit:bool=True):
        """ """
        self._pyHDesk:typing.Optional[PyHDESK]=None
        self.deleteOnExit:bool=False
        if alwaysCreateNew:
            self._pyHDesk=CreateDesktop(desktopName)
            self.deleteOnExit=deleteCreatedOnExit
        else:
            self._pyHDesk=OpenDesktop(desktopName)
            if not self._pyHDesk and createIfMissing:
                self._pyHDesk=CreateDesktop(desktopName)
                self.deleteOnExit=deleteCreatedOnExit
        self.desktopName:str=desktopName

    @property
    def hDesktop(self)->int:
        """
        Handle to the desktop
        """
        if self._pyHDesk is None:
            return 0
        return self._pyHDesk.handle

    @property
    def hWnd(self)->int:
        """
        Handle to the desktop window
        """
        return self.hDesktop

    @property
    def name(self)->str:
        """
        The name of the desktop
        """
        return self.desktopName

    def switchTo(self)->None:
        """
        Make this the currently-selected desktop
        """
        if self._pyHDesk is None:
            raise IndexError("Desktop switching not available")
        self._pyHDesk.SwitchDesktop(self.hDesktop)

    @property
    def hwnd(self):
        """
        get the window handle of this desktop
        """

    def close(self):
        """
        close this desktop

        (will be closed when object goes out of scope as well,
        so you can simply do myDesktopVariable=None instead)
        """
        if self._pyHDesk is not None:
            if self.deleteOnExit:
                self._pyHDesk.CloseDesktop()
            else:
                self._pyHDesk.Detach()
            self._pyHDesk=None

    def __del__(self):
        self.close()

    def getImage(self):
        """
        See also:
            https://social.msdn.microsoft.com/Forums/en-US/4fc9cace-be9f-49b1-8b9f-94cffb4b0fe8/capture-bmp-from-hidden-desktop?forum=windowsgeneraldevelopmentissues

        TODO: this is currently in pseudocode.  Needs to be tested/corrected.
        """
        wndDc=GetWindowDC(self.hwnd)
        memDc=CreateCompatibleDC(wndDc)
        rect=GetWindowRect(self.hwnd)
        memBmp=CreateCompatibleBitmap(wndDc, rect.Width(),rect.Height())
        oldBmp=SelectObject(memDc,memBmp)
        # print(window to the memory DC.)
        BringWindowToTop(self.hwnd,memDc,0)
        # Here you can use memDc of the window
        # (e.g. BitBlt it to the DC of the merged desktop screen)
        DeleteObject(memBmp)
        DeleteDC(wndDc)
        SelectObject(memDc,oldBmp)
        DeleteDC(memDc)
UIDesktop=UiDesktop
VirtualDesktop=UiDesktop
Desktop=UiDesktop


def cmdline(args:typing.Iterable[str]):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printHelp=False
    if not args:
        printHelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                kv=[a.strip() for a in arg.split('=',1)]
                if kv[0] in ['-h','--help']:
                    printHelp=True
                else:
                    print('ERR: unknown argument "'+kv[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printHelp:
        print('Usage:')
        print('  windowsVirtualDesktop.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
