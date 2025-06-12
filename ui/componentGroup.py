"""
something that contains a group of ui items,
but is not necessarily a ui item itself

(for instance, search results, or a logical grouping of windows)
"""
import typing
import re
if typing.TYPE_CHECKING:
    from .component import UiComponent


class UiComponentGroup:
    """
    something that contains a group of ui items,
    but is not necessarily a ui item itself

    (for instance, search results, or a logical grouping of windows)
    """
    def __init__(self):
        self._children:typing.Optional[typing.List["UiComponent"]]=None
        self._childrenLookup:typing.Optional[
            typing.Dict[str,"UiComponent"]]=None

    def findChildren(self,
        matching:typing.Optional[typing.Pattern]=None
        )->typing.Generator["UiComponent",None,None]:
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
    def children(self)->typing.Iterable["UiComponent"]:
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
    def childrenLookup(self)->typing.Dict[str,"UiComponent"]:
        """
        Get the children as a dict
        """
        if self._childrenLookup is None:
            self._childrenLookup={}
            _=self.children
        return self._childrenLookup

    def __getitem__(self,
        idx:typing.Union[int,str]
        )->typing.Optional["UiComponent"]:
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
    def __setitem__(self,idx:str,value:"UiComponent"):
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

UIItemGroup=UiComponentGroup
UIControlGroup=UiComponentGroup
UIComponentGroup=UiComponentGroup
UiItemGroup=UiComponentGroup
UiControlGroup=UiComponentGroup
ComponentGroup=UiComponentGroup
ControlGroup=UiComponentGroup


class UiGroupWithTabs(UiComponentGroup):
    """
    A ui group that contains tabs
    """

    def __init__(self):
        UiComponentGroup.__init__(self)

    @property
    def tabs(self)->UiComponentGroup:
        """
        gather all view tabs from all windows
        """
        ret=UiComponentGroup()
        print(self.tabs)
        ret._childrenLookup=self.__dict__['tabs'] # noqa: E501 # pylint: disable=protected-access
        for c in self.children:
            if c.isTab:
                ret[c.tabName]=c
            else:
                for cc in c.children:
                    if cc.isTab:
                        ret[cc.tabName]=cc
        return ret

UIGroupWithTabs=UiGroupWithTabs
