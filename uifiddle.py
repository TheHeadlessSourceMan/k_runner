"""
resources for controlling the ui
"""
import typing
import re
import time
try:
    import win32gui
    import win32con
    import win32api
    hasWindowsTools=True
except ImportError:
    hasWindowsTools=False

# https://mhammond.github.io/pywin32/
# https://mhammond.github.io/pywin32/win32gui.html
# https://mhammond.github.io/pywin32/win32api.html
# https://docs.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes?redirectedfrom=MSDN
# automating excel and stuff https://pbpython.com/windows-com.html
# controlling explorer windows
# https://stackoverflow.com/questions/43949747/return-a-list-of-all-files-from-the-selected-explorer-window-with-pywin32
# https://stackoverflow.com/questions/21241708/python-get-a-list-of-selected-files-in-explorer-windows-7/21250927#21250927
# hooking into wscript (and controlling windows)
# https://win32com.goermezer.de/microsoft/windows/controlling-applications-via-sendkeys.html


class UiItemGroup:
    """
    something that contains a group of ui items,
    but is not necessarily a ui item itself

    (for instance, search results, or a logical grouping of windows)
    """
    def __init__(self):
        self._children:typing.Optional[typing.List["UiItem"]]=None
        self._childrenLookup:typing.Optional[typing.Dict[str,"UiItem"]]=None

    def findChildren(self,
        matching:typing.Optional[typing.Pattern]=None
        )->typing.Generator["UiItem",None,None]:
        """
        lookup all child windows

        unlike the .children member, this does not cache

        NOTE: do not set _children directly with this!
        """
        if matching is not None and isinstance(matching,str):
            matching=re.compile(matching,re.DOTALL)
        for c in self.children:
            yield c

    @property
    def children(self)->typing.Iterable["UiItem"]:
        """
        NOTE: to get the children, will internally call self.findChildren()
        """
        if self._children is None:
            self._children=[]
            self._childrenLookup={}
            for c in self.findChildren():
                self._children.append(c)
                self._childrenLookup[c.title]=c
        return self._children
    @property
    def childrenLookup(self)->typing.Dict[str,"UiItem"]:
        """
        Get the children as a dict
        """
        if self._childrenLookup is None:
            self._childrenLookup={}
            _=self.children
        return self._childrenLookup

    def __getitem__(self,idx:typing.Union[int,str])->typing.Optional["UiItem"]:
        """
        access like a list or dict
        """
        if isinstance(idx,int):
            for i,c in enumerate(self.children):
                if i==idx:
                    return c
            raise IndexError()
        if isinstance(idx,str):
            children=self.children
            ret=self.childrenLookup.get(idx)
            if ret is not None:
                return ret
            # resort to fuzzy matching
            for c in children:
                if c==idx:
                    return c
        return None
    def __setitem__(self,idx:str,value:"UiItem"):
        _=self.children
        if self._children is None or self._childrenLookup is None:
            raise Exception("Should never get here")
        current=self._childrenLookup.get(idx)
        if current is None:
            # add new to array
            self._children.append(value)
        else:
            # replace existing in array
            currentIdx=self._children.index(current)
            self._children[currentIdx]=value
        self._childrenLookup[idx]=value

    def __len__(self)->int:
        _=self.children
        if self._children is None:
            raise Exception("Should never get here")
        return len(self._children)


class UiItem(UiItemGroup):
    """
    A ui comopnent
    """
    def __init__(self,hwnd):
        UiItemGroup.__init__(self)
        self.hwnd=hwnd
        self._title:typing.Optional[str]=None
        self._text:typing.Optional[str]=None
        self._className:typing.Optional[str]=None

    @property
    def text(self)->str:
        """
        Get/set the item text
        """
        if self._text is None:
            self._text=win32gui.GetWindowText(self.hwnd)
        return self._text
    @text.setter
    def text(self,text:typing.Any):
        self._text=None
        text=str(text)
        win32gui.SetWindowText(self.hwnd)

    @property
    def name(self)->str:
        """
        The name of this component
        """
        return self.title

    @property
    def className(self):
        """
        The class name of this ui component
        """
        if self._className is None:
            self._className=str(win32gui.GetClassName(self.hwnd))
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
            if win32gui.GetParent(hwnd)==self.hwnd:
                if matching is None or matching.match(self.title):
                    children.append(UiItem(hwnd))
        if self.hwnd is not None and self.hwnd:
            win32gui.EnumChildWindows(self.hwnd,winEnumHandler,None)
        for c in children:
            yield c

    def click(self,
        button:str='left',
        count:int=1,
        position:typing.Optional[typing.Tuple[int,int]]=None):
        """
        click on it

        TODO: is not working!
        """
        if position is None:
            position=0,0
        oldPosition=win32api.GetCursorPos()
        oldWindow=win32gui.GetForegroundWindow()
        win32gui.ShowWindow(self.hwnd,win32con.SW_RESTORE)
        #clientPosition=win32gui.ClientToScreen(self.win_handle,position)
        #position=self.__calculate_absolute_coordinates__(clientPosition)
        #win32api.mouse_event(
        # win32con.MOUSEEVENTF_MOVE|win32con.MOUSEEVENTF_ABSOLUTE,
        # position[0],position[1],0,0)
        for _ in range(count):
            if button=='right':
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_RIGHTDOWN,
                    position[0],position[1],0,0)
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_RIGHTUP,
                    *position[0],position[1],0,0)
            elif button=='middle':
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_MIDDLEDOWN,
                    position[0],position[1],0,0)
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_MIDDLEUP,
                    position[0],position[1],0,0)
            else:
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_LEFTDOWN,
                    position[0],position[1],0,0)
                win32api.mouse_event(
                    win32con.MOUSEEVENTF_LEFTUP,
                    position[0],position[1],0,0)
            time.sleep(0.05)
        win32api.SetCursorPos(oldPosition)
        win32gui.SetActiveWindow(oldWindow)

    def sendKeys(self,keycodes:str):
        r"""
        type some stuff

        supports stuff like [ctrl][enter][esc]... as well as characters
            (Delimiter for protected values is "\")

        TODO:
            win32con.VK_NEXT
        """
        raise NotImplementedError()
        #for c in keycodes:
            #win32api.SendMessage(
            # self.hwnd,
            # win32con.WM_CHAR,
            # VkKeyScan(c),
            # 0) # used to use ord() but switched to VkKeyScan()
            #win32gui.SendMessage(self.hwnd,win32con.WM_KEYDOWN,c,0)
            #win32gui.SendMessage(self.hwnd,win32con.WM_KEYUP,c,0)

    def __eq__(self,other:object)->bool:
        """
        compare if this is equal to another UiItem, a cleanTitle, or a hwnd
        """
        if isinstance(other,int):
            return self.hwnd==other
        if isinstance(other,UiItem):
            return self.hwnd==other.hwnd
        if isinstance(other,str):
            return self.titleMatches(other)
        return False

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
        return (self.hwnd is not None) and self.hwnd

    @property
    def title(self):
        """
        Get the component title
        """
        if not self.isValid:
            return ''
        if self._title is None:
            self._title=win32gui.GetWindowText(self.hwnd).strip()
        return self._title

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

    @property
    def visible(self)->bool:
        """
        Is the item visible?
        """
        if not self.isValid:
            return False
        return win32gui.IsWindowVisible(self.hwnd)

    def __repr__(self):
        return f'[{self.hwnd}] {self.className} "{self.title}"'


class UiGroupWithTabs(UiItemGroup):
    """
    A ui group that contains tabs
    """

    def __init__(self):
        UiItemGroup.__init__(self)

    @property
    def tabs(self)->UiItemGroup:
        """
        gather all view tabs from all windows
        """
        ret=UiItemGroup()
        print(self.tabs)
        ret._childrenLookup=self.__dict__['tabs']
        for c in self.children:
            if c.isTab:
                ret[c.tabName]=c
            else:
                for cc in c.children:
                    if cc.isTab:
                        ret[cc.tabName]=cc
        return ret


class Window(UiGroupWithTabs,UiItem):
    """
    A window is a UiItem with the possiblility of having tabs
    along with just children
    """

    def __init__(self,hwnd):
        UiGroupWithTabs.__init__(self)
        UiItem.__init__(self,hwnd)

    def bringToFront(self):
        """
        Bring the window to front
        """
        win32gui.ShowWindow(self.hwnd,5)
        win32gui.SetForegroundWindow(self.hwnd)


def getTopLevelWindows(
    matching:typing.Pattern=None
    )->typing.Generator[Window,None,None]:
    """
    Get all the application windows matching a given pattern
    """
    if matching is not None and isinstance(matching,str):
        matching=re.compile(matching,re.DOTALL)
    children=[]
    def winEnumHandler(hwnd,ctx):
        _=ctx
        if win32gui.IsWindowVisible(hwnd):
            title=win32gui.GetWindowText(hwnd).strip()
            if matching is None or matching.match(title):
                children.append(Window(hwnd))
    win32gui.EnumWindows(winEnumHandler,None)
    for c in children:
        yield c
