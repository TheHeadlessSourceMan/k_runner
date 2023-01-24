#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This program captures a window as an image.  It can even be a "hidden" window!
"""
from ctypes import windll
import win32con
import win32gui
import win32ui
import win32process


HWND=int


class WindowScreenshot:
    """
    This program captures a window as an image.  It can even be a "hidden" window!

    See:
        https://www.codeproject.com/articles/20651/capturing-minimized-window-a-kid-s-trick
        https://stackoverflow.com/questions/5836176/docking-window-inside-another-window
    """

    def __init__(self):
        pass

    def setMinimizeAnimation(self,hWnd:HWND,status:bool=True):
        """
        set the minimize animation status
        """
        old=win32gui.SystemParametersInfo(win32con.SPI_GETANIMATION,None,None)
        if old!=status:
            win32gui.SystemParametersInfo(win32con.SPI_SETANIMATION,status,win32con.SPIF_SENDCHANGE)
        return old==1

    def setTransparency(self,hWnd:HWND,transp:bool=True):
        """
        NOTE: there are several settings involved in this, so returning a True/False
            may contain assumptions that are not true!

        returns the original value
        """
        wlong=win32gui.GetWindowLong(hWnd,win32con.GWL_EXSTYLE)
        colorkey,alpha,flags=win32gui.GetLayeredWindowAttributes(hWnd)
        old=(wlong|win32con.WS_EX_LAYERED)>0 and alpha==1 and (flags|win32con.WS_EX_LAYERED)>0
        if old!=transp:
            if transp:
                win32gui.SetWindowLong(
                    hWnd,win32con.GWL_EXSTYLE,wlong|win32con.WS_EX_LAYERED)
                win32gui.SetLayeredWindowAttributes(hWnd,0,1,flags|win32con.LWA_ALPHA)
            else:
                win32gui.SetWindowLong(
                    hWnd,win32con.GWL_EXSTYLE,wlong&(0xfffffffffffffff|win32con.WS_EX_LAYERED))
                win32gui.SetLayeredWindowAttributes(
                    hWnd,0,0,flags&(0xfffffffffffffff&win32con.LWA_ALPHA))
        return old

    def minimize(self,hWnd:HWND,setMin:bool=True):
        """
        returns the original value
        """
        old=win32process.GetStartupInfo().wShowWindow|win32con.SW_MINIMIZE
        if old!=setMin:
            if setMin:
                win32gui.ShowWindow(hWnd,win32con.SW_MINIMIZE)
            else:
                win32gui.ShowWindow(hWnd,win32con.SW_RESTORE)
        return old

    def _printWindow(self,hWnd:HWND):
        """
        returns PIL image
        """
        import PIL.Image
        rect=win32gui.GetWindowRect(hWnd)
        w=rect[2]-rect[0]
        h=rect[3]-rect[1]
        dc=win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        windll.user32.PrintWindow(hWnd,dc.GetSafeHdc(),0)
        bmp=win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(dc,w,h)
        bitmapbits=bmp.GetBitmapBits(True)
        img=PIL.Image.frombuffer('RGBA',(w,h),bitmapbits,'raw','BGRA',0,1)
        return img

    def _capture(self,hWnd:HWND,getChildren:bool=True)->'PIL.Image':
        """
        do the actual capturing
        """
        img=self._printWindow(hWnd)
        if getChildren:
            pass # TODO: try win32gui.EnumChildWindows()
        return img

    def capture(self,hWnd:HWND,getChildren:bool=True)->'PIL.Image':
        """
        Capture the window contents to an image
        """
        oldMinAnimation=self.setMinimizeAnimation(hWnd,False)
        oldTransparency=self.setTransparency(hWnd,True)
        oldMin=self.minimize(hWnd,False)
        img=self._capture(hWnd,getChildren)
        self.minimize(hWnd,oldMin)
        self.setTransparency(hWnd,oldTransparency)
        self.setMinimizeAnimation(hWnd,oldMinAnimation)
        return img


def cmdline(args):
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
                    print(('ERR: unknown argument "'+arg[0]+'"'))
            else:
                print(('ERR: unknown argument "'+arg+'"'))
    if printhelp:
        print('Usage:')
        print('   windowScreenshot.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])