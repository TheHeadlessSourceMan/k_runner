"""
A ui control comopnent
"""
from pathlib import Path
import typing
import os
import time
import re
if os.name=='nt':
    import win32gui
    import win32api
    import win32con
    import win32process
    from ctypes import windll
from .componentGroup import UiComponentGroup # noqa: E501 # pylint: disable=wrong-import-position
from .keyboardKeys import sendKeyboardKey,sendKeyboardKeys # noqa: E501 # pylint: disable=wrong-import-position
if typing.TYPE_CHECKING:
    from .asUiComponent import UIComponentCompatible
    from k_runner.processes.process import Process
    import PIL.Image


class UiComponent(UiComponentGroup):
    """
    A ui control comopnent.

    You can either find or create a UiComponent and
    do as you will with it, or derive from UiComponent
    with a member called hWnd, that the manipulator will operate on.
    """
    def __init__(self,
        hWnd:"UIComponentCompatible",
        parentWindow:typing.Optional["UiComponent"]=None):
        """ """
        UiComponentGroup.__init__(self)
        if not isinstance(hWnd,int):
            from .asUiComponent import asUiComponent
            hWnd=asUiComponent(hWnd).hWnd
        self.hWnd:int=hWnd
        self._process:typing.Optional['Process']
        self._pid:typing.Optional[int]
        self.parentWindow=parentWindow
        self._title:typing.Optional[str]=None
        self._text:typing.Optional[str]=None
        self._className:typing.Optional[str]=None

    @property
    def hwnd(self)->int:
        """
        alias of hWnd
        """
        return self.hWnd

    @property
    def parent(self)->typing.Optional["WindowManipulator"]:
        """
        Parent of the current window
        """
        return self.parentWindow

    def getWindowTitle(self)->str:
        """
        title of the window
        """
        if os.name=='nt':
            return win32gui.GetWindowText(self.hWnd)
        raise NotImplementedError(f'Not implemented on os="{os.name}"')
    @property
    def windowTitle(self)->str:
        """
        title of the window
        """
        return self.getWindowTitle()
    @property
    def title(self)->str:
        """
        title of the window
        """
        return self.getWindowTitle()
    @property
    def name(self)->str:
        """
        title of the window
        """
        return self.getWindowTitle()

    def getWindowVisible(self)->bool:
        """
        Is the window visible?
        """
        if os.name=='nt':
            return win32gui.IsWindowVisible(self.hWnd)
        raise NotImplementedError(f'Not implemented on os="{os.name}"')
    @property
    def visible(self)->bool:
        """
        Is the item visible?
        """
        if not self.isValid:
            return False
        return win32gui.IsWindowVisible(self.hWnd)

    def setWindowFocus(self)->None:
        """
        Set the current input focus to this window
        """
        if os.name=='nt':
            return win32gui.SetFocus(self.hWnd)
        raise NotImplementedError(f'Not implemented on os="{os.name}"')

    def getChildComponents(self)->typing.Iterable["UiComponent"]:
        """
        Get the child components of this component
        """
        if os.name=='nt':
            results=[]
            def cb(hwnd,results):
                results.append(UiComponent(hwnd,self))
            win32gui.EnumChildWindows(self.hWnd,cb,results)
            return results
        raise NotImplementedError(f'Not implemented on os="{os.name}"')
    @property
    def childComponents(self)->typing.Iterable["UiComponent"]:
        """
        Get the child components of this component
        """
        return self.getChildComponents()
    def getChildWindows(self)->typing.Iterable["UiComponent"]:
        """
        Get the child components of this component
        """
        return self.getChildComponents()
    @property
    def childWindows(self)->typing.Iterable["WindowManipulator"]:
        """
        Get the child components of this component
        """
        return self.getChildComponents()
    @property
    def children(self)->typing.Iterable["WindowManipulator"]:
        """
        Get the child components of this component
        """
        return self.getChildComponents()

    def findChildWindows(self,
        title:typing.Union[typing.Pattern,str,None]=None,
        recursive:bool=False
        )->typing.Generator["WindowManipulator",None,None]:
        """
        Find child windows in a width-first traversal
        """
        tape=list(self.getChildWindows())
        for item in tape:
            if recursive:
                tape.extend(item.getChildWindows())
            # anything we are searching on that doesn't match
            # will continue
            if title is not None:
                if isinstance(title,str):
                    if item.title.lower().find(title.lower())<0:
                        continue
                elif title.match(item.title) is None:
                    continue
            # we never excluded anything, so it passes the test
            yield item
    find=findChildWindows

    @property
    def path(self)->str:
        """
        Path made up of window names
        """
        tape=['']
        self._getPath(tape)
        return '/'.join(tape)
    def _getPath(self,tape:typing.List[str])->None:
        tape.append(self.name)
        if self.parent is not None:
            self.parent._getPath(tape) # pylint: disable = protected-access

    @property
    def tree(self)->str:
        """
        Printable tree of this window and all of its children
        """
        tape:typing.List[str]=[]
        self._tree(tape)
        return '\n'.join(tape)
    def _tree(self,tape:typing.List[str],indent:str=''):
        tape.append(indent+repr(self))
        for c in self.children:
            c._tree(tape,indent+'   ') # pylint: disable = protected-access

    @property
    def root(self)->'UiComponent':
        """
        The uppermost window root of this component
        """
        if self.parent is not None:
            return self.parent.root
        return self

    def click(self,
        button:str="left",
        count=1,
        clickSpeedSec=0.1,
        position:typing.Optional[typing.Tuple[int,int]]=None,
        metaKeys:typing.Optional[typing.Iterable[str]]=None
        )->None:
        """
        Click on this component
        """
        if position is None:
            position=0,0
        button=button[0].lower()
        if os.name=='nt':
            if button=='r':
                dn=win32con.MOUSEEVENTF_RIGHTDOWN
                up=win32con.MOUSEEVENTF_RIGHTUP
            elif button in ('m','c'):
                dn=win32con.MOUSEEVENTF_MIDDLEDOWN
                up=win32con.MOUSEEVENTF_MIDDLEUP
            else: # button=='l':
                dn=win32con.MOUSEEVENTF_LEFTDOWN
                up=win32con.MOUSEEVENTF_LEFTUP
            oldPosition=win32api.GetCursorPos()
            oldWindow=win32gui.GetForegroundWindow()
            win32gui.ShowWindow(self.hWnd,win32con.SW_RESTORE)
            #clientPosition=win32gui.ClientToScreen(self.win_handle,position)
            #position=self.__calculate_absolute_coordinates__(clientPosition)
            #win32api.mouse_event(
            # win32con.MOUSEEVENTF_MOVE|win32con.MOUSEEVENTF_ABSOLUTE,
            # position[0],position[1],0,0)
            x,y=position
            for n in range(count):
                if n>0:
                    time.sleep(clickSpeedSec)
                win32api.mouse_event(dn,x,y)
                time.sleep(clickSpeedSec)
                win32api.mouse_event(up,x,y)
            win32api.SetCursorPos(oldPosition)
            win32gui.SetActiveWindow(oldWindow)
        else:
            raise NotImplementedError()

    def sendKeyboardKeys(self,
        keyStream:str,
        inBackground:bool=False,
        timeDelaySec:float=0.05
        )->None:
        r"""
        Send keyboard keys to the component

        :keyStream: Supports:
            Normal letters
            special keys "[UP_ARROW]"
            meta keys "[CTRL+C]"
            and "[" key via "\["
        :inBackground: Attempt to send to a background
            window without making it foreground first. This
            is unreliable due to windows limitations, but
            could be nice in some cases.
        :timeDelaySec: Time delay between keypresses
        """
        sendKeyboardKeys(keyStream,self.hWnd,inBackground,timeDelaySec)
    sendKeyboard=sendKeyboardKeys
    pressKeys=sendKeyboardKeys
    sendKeys=sendKeyboardKeys

    def sendKeyboardKey(self,
        keyCode:typing.Union[int,str],
        inBackground:bool=False
        )->None:
        """
        Press one single keyboard key

        :keyCode: Supports:
            A single char text key "s"
            key names (with/without []) "PAGE_UP"
            meta keys "CTRL+C"
        :inBackground: Attempt to send to a background
            window without making it foreground first. This
            is unreliable due to windows limitations, but
            could be nice in some cases.

        NOTE: if you want more complicated sequences, you may
        want to try pressKeys() instead.
        """
        sendKeyboardKey(keyCode,self.hWnd,inBackground)
    sendKeyboard=sendKeyboardKey
    pressKey=sendKeyboardKey
    sendKey=sendKeyboardKey

    def setMinimized(self,minimize:bool=True)->None:
        """
        Minimize the window
        """
        if os.name=='nt':
            if minimize:
                win32gui.ShowWindow(self.hWnd,win32con.SW_MINIMIZE)
            else:
                win32gui.ShowWindow(self.hWnd,win32con.SW_RESTORE)
        else:
            raise NotImplementedError()
    minimize=setMinimized

    def setMaximized(self,maximize:bool=True)->None:
        """
        Maximize this window
        """
        if os.name=='nt':
            if maximize:
                win32gui.ShowWindow(self.hWnd,win32con.SW_MAXIMIZE)
            else:
                win32gui.ShowWindow(self.hWnd,win32con.SW_RESTORE)
        else:
            raise NotImplementedError()
    maximize=setMaximized

    @property
    def minimized(self)->bool:
        """
        Get/set the minimized state of the window
        """
        if os.name=='nt':
            startupInfo=win32process.GetStartupInfo()
            return startupInfo.wShowWindow|win32con.SW_MINIMIZE
        else:
            raise NotImplementedError()
    @minimized.setter
    def minimized(self,minimize:bool):
        if os.name=='nt':
            if minimize:
                win32gui.ShowWindow(self.hWnd,win32con.SW_MINIMIZE)
            else:
                win32gui.ShowWindow(self.hWnd,win32con.SW_RESTORE)
        else:
            raise NotImplementedError()

    @property
    def maximized(self)->bool:
        """
        Get/set the maximized state of the window
        """
        if os.name=='nt':
            startupInfo=win32process.GetStartupInfo()
            return startupInfo.wShowWindow|win32con.SW_MAXIMIZE
        else:
            raise NotImplementedError()
    @maximized.setter
    def maximized(self,maximize:bool):
        if os.name=='nt':
            if maximize:
                win32gui.ShowWindow(self.hWnd,win32con.SW_MAXIMIZE)
            else:
                win32gui.ShowWindow(self.hWnd,win32con.SW_RESTORE)
        else:
            raise NotImplementedError()

    def restore(self)->None:
        """
        Restore this window from minimized state
        """
        if os.name=='nt':
            win32gui.ShowWindow(self.hwnd,win32con.SW_RESTORE)
        else:
            raise NotImplementedError()

    def close(self)->None:
        """
        Close this window
        """
        win32gui.PostMessage(self.hwnd,win32con.WM_CLOSE,0,0)
    def closeWindow(self)->None:
        """
        Close the window
        """
        if os.name=='nt':
            win32gui.CloseWindow(self.hWnd)
        else:
            raise NotImplementedError(f'Not implemented on os="{os.name}"')

    def makeForeground(self)->None:
        """
        Bring any associated window to the top

        NOTE: Be a good citizen and use this sparingly!
        """
        win32gui.ShowWindow(self.hwnd,5)
        win32gui.SetForegroundWindow(self.hwnd)
    bringToFront=makeForeground
    makeWindowForeground=makeForeground

    @property
    def pid(self)->int:
        """
        Get the process id for this component
        """
        if self._pid is None:
            from k_runner.processes.find import getPidByHwnd
            self._pid=getPidByHwnd(self.hwnd)
        return self._pid

    @property
    def process(self)->'Process':
        """
        Get the process for this component
        """
        if self._process is None:
            from k_runner.processes.process import Process
            self._process=Process(self.pid)
        return self._process

    def __eq__(self,__o:object)->bool:
        """
        compare if this is equal to another UiItem, a cleanTitle, or a hwnd
        """
        if isinstance(__o,str):
            return self.hwnd==int(__o) or self.titleMatches(__o)
        elif isinstance(__o,int):
            return self.hwnd==__o
        elif hasattr(__o,'hwnd'):
            return self.hwnd==__o.hwnd # type: ignore
        return False

    def getWindowLayout(self)->typing.Tuple[int,int,int,int]:
        """
        Get the layout of the window
        """
        if os.name=='nt':
            return win32gui.GetWindowPlacement(self.hWnd)
        raise NotImplementedError(f'Not implemented on os="{os.name}"')
    def setWindowLayout(self,
        layout:typing.Tuple[
            typing.Optional[int],
            typing.Optional[int],
            typing.Optional[int],
            typing.Optional[int]]
        )->None:
        """
        Get the layout of the window
        """
        if os.name=='nt':
            win32gui.SetWindowPos(self.hWnd,*layout)
        else:
            raise NotImplementedError(f'Not implemented on os="{os.name}"')
    @property
    def windowLayout(self)->typing.Tuple[int,int,int,int]:
        """
        the layout of the window
        """
        return self.getWindowLayout()
    @windowLayout.setter
    def windowLayout(self,windowLayout:typing.Tuple[int,int,int,int]):
        """
        the layout of the window
        """
        return self.setWindowLayout(windowLayout)
    @property
    def layout(self)->typing.Tuple[int,int,int,int]:
        """
        the layout of the window
        """
        return self.getWindowLayout()
    @layout.setter
    def layout(self,windowLayout:typing.Tuple[int,int,int,int]):
        """
        the layout of the window
        """
        return self.setWindowLayout(windowLayout)

    def getWindowLocation(self)->typing.Tuple[int,int]:
        """
        Location of the window
        """
        layout=self.getWindowLayout()
        return (layout[0],layout[1])
    def setWindowLocation(self,location:typing.Tuple[int,int])->None:
        """
        Location of the window
        """
        self.setWindowLayout((location[0],location[1],None,None))
    @property
    def windowLocation(self)->typing.Tuple[int,int]:
        """
        Location of the window
        """
        return self.getWindowLocation()
    @windowLocation.setter
    def windowLocation(self,windowLocation:typing.Tuple[int,int]):
        """
        Location of the window
        """
        return self.setWindowLocation(windowLocation)
    @property
    def location(self)->typing.Tuple[int,int]:
        """
        Location of the window
        """
        return self.getWindowLocation()
    @location.setter
    def location(self,windowLocation:typing.Tuple[int,int]):
        """
        Location of the window
        """
        return self.setWindowLocation(windowLocation)

    def getWindowSize(self)->typing.Tuple[int,int]:
        """
        Size of the window
        """
        layout=self.getWindowLayout()
        return (layout[2],layout[3])
    def setWindowSize(self,size:typing.Tuple[int,int])->None:
        """
        Size of the window
        """
        self.setWindowLayout((None,None,size[0],size[1]))
    @property
    def windowSize(self)->typing.Tuple[int,int]:
        """
        Size of the window
        """
        return self.getWindowSize()
    @windowSize.setter
    def windowSize(self,size:typing.Tuple[int,int]):
        """
        Size of the window
        """
        return self.setWindowSize(size)
    @property
    def size(self)->typing.Tuple[int,int]:
        """
        Size of the window
        """
        return self.getWindowSize()
    @size.setter
    def size(self,size:typing.Tuple[int,int]):
        """
        Size of the window
        """
        return self.setWindowSize(size)

    @property
    def text(self)->str:
        """
        Get/set the item text
        """
        if self._text is None:
            self._text=win32gui.GetWindowText(self.hWnd)
        return self._text # type: ignore
    @text.setter
    def text(self,text:typing.Any):
        self._text=None
        text=str(text)
        win32gui.SetWindowText(self.hWnd)

    @property
    def className(self):
        """
        The class name of this ui component
        """
        if self._className is None:
            self._className=str(win32gui.GetClassName(self.hWnd))
        return self._className

    def findChildren(self,
        matching:typing.Optional[typing.Pattern]=None
        )->typing.Generator["UiItem",None,None]:
        """
        lookup all child windows

        unlike the .children member, this does not cache

        Reverences:
            https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getancestor
        """
        if matching is not None and isinstance(matching,str):
            matching=re.compile(matching,re.DOTALL)
        children=[]
        def winEnumHandler(hwnd,ctx):
            _=ctx
            if win32gui.GetParent(hwnd)==self.hWnd:
                if matching is None or matching.match(self.title):
                    children.append(UiItem(hwnd))
        if self.hWnd is not None and self.hWnd:
            win32gui.EnumChildWindows(self.hWnd,winEnumHandler,None)
        for c in children:
            yield c

    def titleMatches(self,other:str)->bool:
        """
        cleans up both titles, then compares
        """
        def clean(
            s:str,
            removeAllBefore=None,
            removeAllAfter=('SAMPLE:','-')
            )->str:
            """ """
            if removeAllAfter is not None:
                if isinstance(removeAllAfter,str):
                    removeAllAfter=[removeAllAfter]
                for rm in removeAllAfter:
                    s=s.split(rm,1)[0]
            if removeAllBefore is not None:
                if isinstance(removeAllBefore,str):
                    removeAllBefore=[removeAllBefore]
                for rm in removeAllBefore:
                    s=s.rsplit(rm,1)[-1]
            s=s.strip()
            s=ignoreParens(s,'()')
            s=ignoreParens(s,'[]').strip()
            for c in ' -_"':
                s=s.replace(c,'')
            return s.lower()
        def ignoreParens(s:str,parens='()')->str:
            ss=s.split(parens[0])
            if len(ss)>1:
                sList:typing.List[str]=[]
                for sss in ss:
                    if not s:
                        sList=[sss]
                    else:
                        sssList=sss.rsplit(parens[-1],1)
                        if len(sssList)>1:
                            sList.append(sssList[1])
                s=''.join(sList)
            return s
        return clean(self.title)==clean(other)

    @property
    def isValid(self):
        """
        Is the item valid?
        """
        return (self.hWnd is not None) and self.hWnd

    @property
    def isTab(self)->bool:
        """
        Is the item a tab?
        """
        return self.title.find('[')>0

    @property
    def tabName(self)->str:
        """
        If it's a tab, what's the name?
        """
        return self.title.split('[',1)[0].strip()

    def setMinimizeAnimation(self,hWnd:int,status:bool=True)->bool:
        """
        set the minimize animation status
        """
        _=hWnd
        old=win32gui.SystemParametersInfo(win32con.SPI_GETANIMATION,None,None)
        if old!=status:
            win32gui.SystemParametersInfo(
                win32con.SPI_SETANIMATION,status,win32con.SPIF_SENDCHANGE)
        return old==1

    def setTransparency(self,hWnd:int,transp:bool=True)->int:
        """
        NOTE: there are several settings involved in this, so returning a
            True/False may contain assumptions that are not true!

        returns the original value
        """
        wlong=win32gui.GetWindowLong(hWnd,win32con.GWL_EXSTYLE)
        colorKey,alpha,flags=win32gui.GetLayeredWindowAttributes(hWnd)
        _=colorKey
        old=(wlong|win32con.WS_EX_LAYERED)>0 \
            and alpha==1 \
            and (flags|win32con.WS_EX_LAYERED)>0
        if old!=transp:
            if transp:
                win32gui.SetWindowLong(
                    hWnd,win32con.GWL_EXSTYLE,wlong|win32con.WS_EX_LAYERED)
                win32gui.SetLayeredWindowAttributes(hWnd,
                    0,1,flags|win32con.LWA_ALPHA)
            else:
                win32gui.SetWindowLong(hWnd,
                    win32con.GWL_EXSTYLE,
                    wlong&(0xfffffffffffffff|win32con.WS_EX_LAYERED))
                win32gui.SetLayeredWindowAttributes(
                    hWnd,0,0,flags&(0xfffffffffffffff&win32con.LWA_ALPHA))
        return old

    def _printWindow(self,hWnd:int)->"PIL.Image.Image":
        """
        returns PIL image
        """
        import PIL.Image
        if os.name=='nt':
            # Import for win32ui is in here because it has been known
            # to get broken from time to time and cause an import error.
            # This way it will only take down one method,
            # not the whole file.
            import win32ui
            rect=win32gui.GetWindowRect(hWnd)
            w=rect[2]-rect[0]
            h=rect[3]-rect[1]
            dc=win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            windll.user32.PrintWindow(hWnd,dc.GetSafeHdc(),0)
            bmp=win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(dc,w,h)
            bitmapBits=bmp.GetBitmapBits(True)
            img=PIL.Image.frombuffer('RGBA',(w,h),bitmapBits,'raw','BGRA',0,1)
        else:
            raise NotImplementedError()
        return img

    def _capture(self,hWnd:int,getChildren:bool=True)->'PIL.Image.Image':
        """
        do the actual capturing
        """
        img=self._printWindow(hWnd)
        if getChildren:
            pass # TODO: try win32gui.EnumChildWindows()
        return img

    def capture(self,getChildren:bool=True)->'PIL.Image.Image':
        """
        Capture the window contents to an image

        See:
            https://www.codeproject.com/articles/20651/capturing-minimized-window-a-kid-s-trick
            https://stackoverflow.com/questions/5836176/docking-window-inside-another-window
        """
        hWnd=self.hWnd
        oldMinAnimation=self.setMinimizeAnimation(hWnd,False)
        oldTransparency=self.setTransparency(hWnd,True)
        oldMin=self.minimized
        self.minimize(False)
        img=self._capture(hWnd,getChildren)
        self.minimize(oldMin)
        self.setTransparency(hWnd,oldTransparency==1)
        self.setMinimizeAnimation(hWnd,oldMinAnimation)
        return img

    def saveScreenshot(self,
        file:typing.Union[str,Path,typing.IO[bytes]],
        getChildren:bool=True
        )->'PIL.Image.Image':
        """
        Save a screenshot of the component to file.

        The file can be a binary buffer or filename.
        """
        img=self.capture(getChildren)
        if isinstance(file,Path):
            file=str(file)
        else:
            img.save(file)
        return img

    def __hash__(self)->int:
        return self.hWnd

    def __repr__(self):
        return f'[{self.hWnd}] {self.className} "{self.title}"'

UIItem=UiComponent
UIControl=UiComponent
UIComponent=UiComponent
UiItem=UiComponent
UiControl=UiComponent
Control=UiComponent
Component=UiComponent
WindowScreenshot=UiComponent # weird legacy name
WindowManipulator=UiComponent # legacy
