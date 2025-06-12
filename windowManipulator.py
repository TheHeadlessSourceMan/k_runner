"""
Tool for manipulation system windows.

You can either create a WindowManipulator and
do as you will with it, or derive from WindowManipulator
with a member called hwnd, that the manipulator will operate on.
"""
import typing
import os
if os.name=='nt':
    import win32gui


class WindowManipulator:
    """
    Tool for manipulation system windows.

    You can either create a WindowManipulator and
    do as you will with it, or derive from WindowManipulator
    with a member called hwnd, that the manipulator will operate on.
    """

    def __init__(self,
        hwnd:typing.Optional[str]=None,
        parentWindow:typing.Optional["WindowManipulator"]=None):
        """ """
        self.hwnd=hwnd
        self.parentWindow=parentWindow

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
            return win32gui.GetWindowText(self.hwnd)
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
            return win32gui.IsWindowVisible(self.hwnd)
        raise NotImplementedError(f'Not implemented on os="{os.name}"')
    @property
    def visible(self)->bool:
        """
        Is the window visible?
        """
        return self.getWindowVisible()

    def setWindowFocus(self)->None:
        """
        Set the current input focus to this window
        """
        if os.name=='nt':
            return win32gui.SetFocus(self.hwnd)
        raise NotImplementedError(f'Not implemented on os="{os.name}"')

    def getChildWindows(self)->typing.Iterable["WindowManipulator"]:
        """
        child windows of this window
        """
        if os.name=='nt':
            results=[]
            def cb(hwnd,results):
                results.append(WindowManipulator(hwnd,self))
            win32gui.EnumChildWindows(self.hwnd,cb,results)
            return results
        raise NotImplementedError(f'Not implemented on os="{os.name}"')
    @property
    def childWindows(self)->typing.Iterable["WindowManipulator"]:
        """
        child windows of this window
        """
        return self.getChildWindows()
    @property
    def children(self)->typing.Iterable["WindowManipulator"]:
        """
        child windows of this window
        """
        return self.getChildWindows()

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

    def click(self,location:tuple[int,int],button='left',metaKeys=None)->None:
        """
        Click on a point on the window
        """
        raise NotImplementedError(f'Not implemented on os="{os.name}"')

    def sendKeys(self,keys:str,metaKeys=None)->None:
        """
        Send keypresses to the window
        """
        raise NotImplementedError(f'Not implemented on os="{os.name}"')

    def closeWindow(self)->None:
        """
        Close the window
        """
        if os.name=='nt':
            win32gui.CloseWindow(self.hwnd)
        else:
            raise NotImplementedError(f'Not implemented on os="{os.name}"')
    close=closeWindow

    def getWindowLayout(self)->typing.Tuple[int,int,int,int]:
        """
        Get the layout of the window
        """
        if os.name=='nt':
            return win32gui.GetWindowPlacement(self.hwnd)
        raise NotImplementedError(f'Not implemented on os="{os.name}"')
    def setWindowLayout(self,layout:typing.Tuple[int,int,int,int])->None:
        """
        Get the layout of the window
        """
        if os.name=='nt':
            win32gui.SetWindowPos(self.hwnd,*layout)
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
