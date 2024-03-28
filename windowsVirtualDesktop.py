#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This program creates a detatched desktop that can be used
as a canvas for remote rendering.
"""
import typing
from win32gui import (
    BringWindowToTop,
    CreateCompatibleBitmap,
    CreateCompatibleDC,
    DeleteDC,
    DeleteObject,
    GetWindowDC,
    GetWindowRect,
    SelectObject)


class Desktop:
    """
    This program creates a detatched desktop that can be used as a canvas for
    remote rendering.
    """

    def __init__(self):
        self.hDesktop=None

    @property
    def hwnd(self):
        """
        get the window handle of this desktop
        """

    def _create(self):
        """
        See also:
            https://msdn.microsoft.com/en-us/library/windows/desktop/ms682127(v=vs.85).aspx
        """
        #TODO: see api, CreateDesktop

    def close(self):
        """
        close this desktop

        (will be closed when object goes out of scope as well,
        so you can simply do myDesktopVariable=None instead)
        """
        if self.hDesktop is not None:
            CloseDesktop(self.hDesktop)
            self.hDesktop=None

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


def cmdline(args:typing.Iterable[str]):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                arg=[a.strip() for a in arg.split('=',1)]
                if arg[0] in ['-h','--help']:
                    printhelp=True
                else:
                    print('ERR: unknown argument "'+arg[0]+'"')
            else:
                print('ERR: unknown argument "'+arg+'"')
    if printhelp:
        print('Usage:')
        print('  windowsVirtualDesktop.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
