"""
This is designed to work with osrun such that it waits until a condition
is matched, then passes on sobsequent messages
"""
import typing
import re

class Expect:
    """
    This is designed to work with osrun such that it waits until a condition
    is matched, then passes on sobsequent messages
    """
    def __init__(self,
        waitFor:typing.Union[str,typing.Pattern,None],
        thenCall:typing.Callable[[str],None],
        untilThis:typing.Union[str,typing.Pattern],
        repeat:bool=True):
        """
        """
        self.thenCall:typing.Callable[[str],None]=thenCall
        self.repeat=repeat
        self._triggered=False
        self._count=0
        if waitFor is None:
            self._triggered=True
            self._count=1
        elif isinstance(waitFor,str):
            self.waitFor=re.compile(waitFor)
        else:
            self.waitFor=waitFor
        if untilThis is not None:
            if isinstance(untilThis,str):
                untilThis=re.compile(untilThis)
        self.untilThis=untilThis

    def addLine(self,s:str)->None:
        """
        Add another expected line
        """
        if self._triggered:
            if self.untilThis is not None:
                if self.untilThis.match(s) is not None:
                    self._triggered=False
            elif self._triggered:
                self.thenCall(s)
        elif self.waitFor is not None:
            if self.repeat is False and self._count>0:
                pass
            elif self.waitFor.match(s) is not None:
                self._triggered=True
                self._count+=1
    __call__=addLine
