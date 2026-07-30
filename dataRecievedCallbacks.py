"""
Types for callbacks to be notified when data is recieved
"""
import typing
import time
import traceback
from threading import Thread
from queue import Queue,Empty
import codecs
from .settings import useDaemonThreads


StringNotify=typing.Callable[[str],None]
StringNotifies=typing.Union[StringNotify,typing.Iterable[StringNotify]]
StringNotifyList=typing.List[StringNotify]


BytesNotify=typing.Callable[[bytes],None]
BytesNotifies=typing.Union[BytesNotify,typing.Iterable[BytesNotify]]
BytesNotifyList=typing.List[BytesNotify]


class DataRecievedCallbacks:
    """
    A group of run callbacks
    """

    STDERR=0
    STDOUT=1
    STDOUTERR=2

    def __init__(self,
        stdouterrLineCallbacks:typing.Optional[StringNotifies]=None,
        stdoutLineCallbacks:typing.Optional[StringNotifies]=None,
        stderrLineCallbacks:typing.Optional[StringNotifies]=None,
        stdouterrCharCallbacks:typing.Optional[StringNotifies]=None,
        stdoutCharCallbacks:typing.Optional[StringNotifies]=None,
        stderrCharCallbacks:typing.Optional[StringNotifies]=None,
        stdouterrBytesCallbacks:typing.Optional[BytesNotifies]=None,
        stdoutBytesCallbacks:typing.Optional[BytesNotifies]=None,
        stderrBytesCallbacks:typing.Optional[BytesNotifies]=None,
        runCallbacks:typing.Optional["DataRecievedCallbacks"]=None):
        """ """
        self._byteNotifiers:typing.Tuple[
            BytesNotifyList,BytesNotifyList,BytesNotifyList]=([],[],[])
        self._charNotifiers:typing.Tuple[
            StringNotifyList,StringNotifyList,StringNotifyList]=([],[],[])
        self._lineNotifiers:typing.Tuple[
            StringNotifyList,StringNotifyList,StringNotifyList]=([],[],[])
        self.extendCallbacks(runCallbacks)
        if stdouterrLineCallbacks is not None:
            self.addLineNotifies(self.STDOUTERR,stdouterrLineCallbacks)
        if stdoutLineCallbacks is not None:
            self.addLineNotifies(self.STDOUT,stdoutLineCallbacks)
        if stderrLineCallbacks is not None:
            self.addLineNotifies(self.STDERR,stderrLineCallbacks)
        if stdouterrCharCallbacks is not None:
            self.addCharNotifies(self.STDOUTERR,stdouterrCharCallbacks)
        if stdoutCharCallbacks is not None:
            self.addCharNotifies(self.STDOUT,stdoutCharCallbacks)
        if stderrCharCallbacks is not None:
            self.addCharNotifies(self.STDERR,stderrCharCallbacks)
        if stdouterrBytesCallbacks is not None:
            self.addBytesNotifies(self.STDOUTERR,stdouterrBytesCallbacks)
        if stdoutBytesCallbacks is not None:
            self.addBytesNotifies(self.STDOUT,stdoutBytesCallbacks)
        if stderrBytesCallbacks is not None:
            self.addBytesNotifies(self.STDERR,stderrBytesCallbacks)

    def assignCallbacks(self,other:typing.Optional["DataRecievedCallbacks"]):
        """
        Assign the callbacks to match another group
        """
        self.clearCallbacks()
        self.extendCallbacks(other)

    def clearCallbacks(self):
        """
        Assign the callbacks to match another group
        """
        self._byteNotifiers=([],[],[])
        self._charNotifiers=([],[],[])
        self._lineNotifiers=([],[],[])

    def extendCallbacks(self,other:typing.Optional["DataRecievedCallbacks"]):
        """
        Assign the callbacks to match another group
        """
        if other is None:
            return
        for streamNum,stream in enumerate(other._byteNotifiers): # noqa:E501 # pylint: disable=protected-access,line-too-long
            self.addBytesNotifies(streamNum,stream)
        for streamNum,stream in enumerate(other._charNotifiers): # noqa:E501 # pylint: disable=protected-access,line-too-long
            self.addCharNotifies(streamNum,stream)
        for streamNum,stream in enumerate(other._lineNotifiers): # noqa:E501 # pylint: disable=protected-access,line-too-long
            self.addLineNotifies(streamNum,stream)

    def addBytesNotifies(self,
        whichStream:int,
        notifies:typing.Optional[BytesNotifies]):
        """
        Add functions to be notified when one or more new bytes are added
        """
        if notifies is None:
            return
        if hasattr(notifies,'__iter__'):
            notifies=typing.cast(typing.Iterable[BytesNotify],notifies)
            self._byteNotifiers[whichStream].extend(notifies)
        else:
            notifies=typing.cast(BytesNotify,notifies)
            self._byteNotifiers[whichStream].append(notifies)
    addBytesNotify=addBytesNotifies

    def removeBytesNotifies(self,whichStream:int,notifies:BytesNotifies):
        """
        Remove functions to be notified when one or more new bytes are added
        """
        try:
            if hasattr(notifies,'__iter__'):
                notifies=typing.cast(typing.Iterable[BytesNotify],notifies)
                for bn in notifies:
                    self._byteNotifiers[whichStream].remove(bn)
            else:
                notifies=typing.cast(BytesNotify,notifies)
                self._byteNotifiers[whichStream].remove(notifies)
        except ValueError:
            pass # this gets thrown when it's not in the list
    removeBytesNotify=removeBytesNotifies

    def addCharNotifies(self,
        whichStream:int,
        notifies:typing.Optional[StringNotifies]):
        """
        Add functions to be notified whenever a new character is added

        NOTE: character type is defined by the stringFormat member
        """
        if notifies is None:
            return
        if hasattr(notifies,'__iter__'):
            notifies=typing.cast(typing.Iterable[StringNotify],notifies)
            self._charNotifiers[whichStream].extend(notifies)
        else:
            notifies=typing.cast(StringNotify,notifies)
            self._charNotifiers[whichStream].append(notifies)
    addCharNotify=addCharNotifies

    def removeCharNotifies(self,
        whichStream:int,
        notifies:StringNotifies):
        """
        Remove functions to be notified whenever a new character is added
        """
        try:
            if hasattr(notifies,'__iter__'):
                notifies=typing.cast(
                    typing.Iterable[StringNotify],notifies)
                for bn in notifies:
                    self._charNotifiers[whichStream].remove(bn)
            else:
                notifies=typing.cast(StringNotify,notifies)
                self._charNotifiers[whichStream].remove(notifies)
        except ValueError:
            pass # this gets thrown when it's not in the list
    removeCharNotify=removeCharNotifies

    def addLineNotifies(self,
        whichStream:int,
        notifies:typing.Optional[StringNotifies]):
        """
        Add functions to be notified whenever a new character is added

        NOTE: character type is defined by the stringFormat member
        """
        if notifies is None:
            return
        if hasattr(notifies,'__iter__'):
            notifies=typing.cast(
                typing.Iterable[StringNotify],notifies)
            self._lineNotifiers[whichStream].extend(notifies)
        else:
            notifies=typing.cast(StringNotify,notifies)
            self._lineNotifiers[whichStream].append(notifies)
    addLineNotify=addLineNotifies

    def removeLineNotifies(self,whichStream:int,notifies:StringNotifies):
        """
        Remove functions to be notified whenever a new character is added
        """
        try:
            if hasattr(notifies,'__iter__'):
                notifies=typing.cast(
                    typing.Iterable[StringNotify],notifies)
                for bn in notifies:
                    self._lineNotifiers[whichStream].remove(bn)
            else:
                notifies=typing.cast(StringNotify,notifies)
                self._lineNotifiers[whichStream].remove(notifies)
        except ValueError:
            pass # this gets thrown when it's not in the list
    removeLineNotify=removeLineNotifies

    def addCallOnStdoutLine(self,
        notifies:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new line of data
        """
        self.addLineNotifies(self.STDOUT,notifies)

    def addCallOnStdoutChar(self,
        notifies:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new char of data
        """
        self.addCharNotifies(self.STDOUT,notifies)

    def addCallOnStderrLine(self,
        notifies:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new line of data
        """
        self.addLineNotifies(self.STDERR,notifies)

    def addCallOnStderrChar(self,
        notifies:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new char of data
        """
        self.addCharNotifies(self.STDERR,notifies)

    def addCallOnStdoutErrLine(self,
        notifies:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new line of data
        """
        self.addLineNotifies(self.STDOUTERR,notifies)

    def addCallOnStdoutErrChar(self,
        notifies:typing.Optional[StringNotifies]=None
        )->None:
        """
        add function(s) to call on new char of data
        """
        self.addCharNotifies(self.STDOUTERR,notifies)


class ApplicationCallbacks(DataRecievedCallbacks):
    """
    For application messages that are not necessarily
    data recieved. (Eg, exit, or some other event)
    """


class RecieveDataManager(DataRecievedCallbacks):
    """
    A class for notifying callbacks on incoming process data

    It also keeps track of the buffers, so once you are done
    appending data, it can be read in many ways, such as:
    getLines(STDERR)
    """

    def __init__(self,
        runCallbacks:typing.Optional[DataRecievedCallbacks]=None,
        stringFormat:str='utf-8'):
        """ """
        DataRecievedCallbacks.__init__(self,runCallbacks=runCallbacks)
        self._keepgoing=True
        self._interleaveStdoutByLine=True # as opposed to by character
        self._pauseNotifications=False
        self._notifyThread:typing.Optional[Thread]=None
        self._stringFormat=stringFormat
        self._decoders=(
            codecs.getincrementaldecoder(self._stringFormat)(),
            codecs.getincrementaldecoder(self._stringFormat)(),
            codecs.getincrementaldecoder(self._stringFormat)())
        self._byteBuffers:typing.Tuple[bytearray,bytearray,bytearray]=\
            (bytearray(),bytearray(),bytearray())
        self._charBuffers:typing.Tuple[
            typing.List[str],typing.List[str],typing.List[str]]=\
            ([],[],[])
        self._currentLineBuffers:typing.Tuple[
            typing.List[str],typing.List[str],typing.List[str]]=\
            ([],[],[])
        self._lineBuffers:typing.Tuple[
            typing.List[str],typing.List[str],typing.List[str]]=\
            ([],[],[])
        self._stdouterrCurrentLineChars:typing.Tuple[
            typing.List[str],typing.List[str]]=\
            ([],[])
        self._notifyQueue=Queue[typing.Tuple[int,bytes]]()

    def getBytes(self,
        whichStream:int=2
        )->typing.Iterable[int]:
        """
        Get as bytes
        """
        if self._notifyThread is None:
            return bytes(self._byteBuffers[whichStream])
        self._pauseNotifications=True
        time.sleep(0.1)
        q=Queue[int]()
        for b in self._byteBuffers[whichStream]:
            q.put(b)
        def cb(value:bytes)->None:
            for v in value:
                q.put(v)
        self.addBytesNotify(whichStream,cb)
        self._pauseNotifications=False
        while self._notifyThread is not None: # type: ignore
            try:
                yield q.get(timeout=0.1)
            except Empty:
                pass

    def getChars(self,
        whichStream:int=2,
        encoding:typing.Optional[str]=None
        )->typing.Iterable[str]:
        """
        Get entire buffer as characters

        If the data stream is running, this behaves slightly
        different than getStr()
        getChars() will iterate over single characters as they come in
        getStr() will sit and wait for the whole string to come in
        """
        if encoding is None:
            encoding=self._stringFormat
        if self._notifyThread is None:
            return ''.join(self._charBuffers[whichStream])
        self._pauseNotifications=True
        time.sleep(0.1)
        q=Queue[str]()
        for c in self._charBuffers[whichStream]:
            q.put(c)
        def cb(value:str):
            q.put(value)
        self.addCharNotify(whichStream,cb)
        self._pauseNotifications=False
        while self._notifyThread is not None: # type: ignore
            try:
                yield from q.get(timeout=0.1)
            except Empty:
                pass
    @property
    def chars(self)->typing.Iterable[str]:
        """
        Get entire buffer as a string of characters
        """
        return self.getChars()

    def getStr(self,
        whichStream:int=2,
        encoding:typing.Optional[str]=None
        )->str:
        """
        Get the full data string.

        If the data stream is running, this behaves slightly
        different than getChars()
        getChars() will iterate over single characters as they come in
        getStr() will sit and wait for the whole string to come in
        """
        if encoding is None:
            encoding=self._stringFormat
        while self._notifyThread is not None:
            time.sleep(0.1)
        return ''.join(self._charBuffers[whichStream])
    getText=getStr
    __str__=getStr
    @property
    def text(self)->str:
        """
        Get entire buffer as a string of characters
        """
        return self.getStr()

    def getStdout(self,
        encoding:typing.Optional[str]=None
        )->str:
        """
        Get stdout buffer as a string of characters
        """
        return self.getStr(self.STDOUT,encoding)
    @property
    def stdout(self)->str:
        """
        Get stdout buffer as a string of characters
        """
        return self.getStr(self.STDOUT)

    def getStderr(self,
        encoding:typing.Optional[str]=None
        )->str:
        """
        Get stderr buffer as a string of characters
        """
        return self.getStr(self.STDERR,encoding)
    @property
    def stderr(self)->str:
        """
        Get stderr buffer as a string of characters
        """
        return self.getStr(self.STDERR)

    def getStdoutLines(self,
        encoding:typing.Optional[str]=None
        )->typing.Iterable[str]:
        """
        Get stdout buffer as a string of characters
        """
        return self.getLines(self.STDOUT,encoding)
    @property
    def stdoutLines(self)->typing.Iterable[str]:
        """
        Get stdout buffer as a string of characters
        """
        return self.getLines(self.STDOUT)

    def getStderrLines(self,
        encoding:typing.Optional[str]=None
        )->typing.Iterable[str]:
        """
        Get stderr buffer as a string of characters
        """
        return self.getLines(self.STDERR,encoding)
    @property
    def stderrLines(self)->typing.Iterable[str]:
        """
        Get stderr buffer as a string of characters
        """
        return self.getLines(self.STDERR)

    def getLines(self,
        whichStream:int=2,
        encoding:typing.Optional[str]=None
        )->typing.Iterable[str]:
        """
        Get buffer as lines of text
        """
        if encoding is None:
            encoding=self._stringFormat
        if self._notifyThread is None:
            return self._lineBuffers[whichStream]
        self._pauseNotifications=True
        time.sleep(0.1)
        q=Queue[str]()
        for line in self._lineBuffers[whichStream]:
            q.put(line)
        def cb(value:str):
            q.put(value)
        self.addLineNotify(whichStream,cb)
        self._pauseNotifications=False
        while self._notifyThread is not None: # type: ignore
            try:
                line=q.get(timeout=0.1)
                yield line
            except Empty:
                pass

    @property
    def lines(self)->typing.Iterable[str]:
        """
        Get buffer as lines of text
        """
        return self.getLines()

    def addBytes(self,whichStream:int,b:bytes)->None:
        """
        Add more bytes to the stdout or stderr stream
        """
        if whichStream==self.STDOUTERR:
            whichStream=self.STDOUT
        self._byteBuffers[self.STDOUTERR].extend(b)
        self._byteBuffers[whichStream].extend(b)
        self._notifyQueue.put((whichStream,b))

    def _notifyBytes(self,whichStream:int,b:bytes)->None:
        """
        Do callbacks for individual bytes
        """
        # Ensure that we are only attempting to decode one at a time
        if len(b)>1:
            for bb in b:
                self._notifyBytes(whichStream,bytes((bb,)))
            return
        # save the byte itself
        for callback in self._byteNotifiers[whichStream]:
            try:
                callback(b)
            except Exception as e:
                traceback.print_exception(e)
                if not hasattr(callback,'__call__'):
                    print(f'Invalid callback type detected: "{type(callback)}"') # noqa:E501 # pylint: disable=line-too-long
                else:
                    print(f'Exception caused callback "{callback.__name__}" to be disabled') # noqa: E501 # pylint: disable=line-too-long
                self._byteNotifiers[whichStream].remove(callback)
        # we'll append the bytes to the combined stream in
        # the order they were received
        for callback in self._byteNotifiers[self.STDOUTERR]:
            try:
                callback(b)
            except Exception as e:
                traceback.print_exception(e)
                if not hasattr(callback,'__call__'):
                    print(f'Invalid callback type detected: "{type(callback)}"') # noqa: E501 # pylint: disable=line-too-long
                else:
                    print(f'Exception caused callback "{callback.__name__}" to be disabled') # noqa: E501 # pylint: disable=line-too-long
                self._byteNotifiers[self.STDOUTERR].remove(callback)
        # attempt to convert to character and do all that stuff
        try:
            c=self._decoders[whichStream].decode(b)
            self._notifyChar(whichStream,c)
            # add the character(s) to the combined stdout/stdin buffer
            if not self._interleaveStdoutByLine:
                # add immediaetly
                self._notifyChar(self.STDOUTERR,c)
            elif c=='\n':
                # this ends a line, so add it
                for c in self._stdouterrCurrentLineChars[whichStream]:
                    self._notifyChar(self.STDOUTERR,c)
                self._notifyChar(self.STDOUTERR,'\n')
                self._stdouterrCurrentLineChars[whichStream].clear()
            else:
                # store it to add when we've got a full line
                self._stdouterrCurrentLineChars[whichStream].append(c)
        except UnicodeDecodeError as e:
            if e.reason!='unexpected end of data':
                raise e

    def _notifyChar(self,whichStream:int,c:str)->None:
        """
        Do callbacks for individual text characters
        """
        for callback in self._charNotifiers[whichStream]:
            try:
                callback(c)
            except Exception as e:
                traceback.print_exception(e)
                if not hasattr(callback,'__call__'):
                    print(f'Invalid callback type detected: "{type(callback)}"') # noqa:E501 # pylint: disable=line-too-long
                else:
                    print(f'Exception caused callback "{callback.__name__}" to be disabled') # noqa:E501 # pylint: disable=line-too-long
                self._charNotifiers[whichStream].remove(callback)
        if c=='\n':
            lb=self._currentLineBuffers[whichStream]
            if lb and lb[-1]=='\r':
                lb.pop()
            line=''.join(lb)
            self._notifyLine(whichStream,line)
            lb.clear()
        else:
            self._currentLineBuffers[whichStream].append(c)

    def _notifyLine(self,whichStream:int,s:str)->None:
        """
        Do callbacks for individual text lines
        """
        for callback in self._lineNotifiers[whichStream]:
            try:
                callback(s)
            except Exception as e:
                traceback.print_exception(e)
                if not hasattr(callback,'__call__'):
                    print(f'Invalid callback type detected: "{type(callback)}"') # noqa:E501 # pylint: disable=line-too-long
                else:
                    print(f'Exception caused callback "{callback.__name__}" to be disabled') # noqa:E501 # pylint: disable=line-too-long
                self._lineNotifiers[whichStream].remove(callback)

    def _finishLineBuffers(self):
        """
        Finish off any line buffers in case
        there was no newline at the end of the file
        """
        for whichStream,lb in enumerate(self._currentLineBuffers):
            if lb:
                self._notifyLine(whichStream,''.join(lb))
                lb.clear()

    def clear(self):
        """
        Clear out all buffers
        """
        self._decoders=(
            codecs.getincrementaldecoder(self._stringFormat)(),
            codecs.getincrementaldecoder(self._stringFormat)(),
            codecs.getincrementaldecoder(self._stringFormat)())
        self._byteBuffers=(bytearray(),bytearray(),bytearray())
        for lb in self._currentLineBuffers:
            lb.clear()

    def _notifyThreadLoop(self):
        """
        Perform the callbacks in a thread
        so they don't block data gathering
        """
        self.clear()
        self._keepgoing=True
        while True:
            if self._pauseNotifications:
                time.sleep(0.01)
                continue
            try:
                self._notifyBytes(
                    *self._notifyQueue.get(timeout=0.2))
            except Empty:
                if not self._keepgoing:
                    self._finishLineBuffers()
                    break

    def start(self):
        """
        Start notifying
        """
        if self._notifyThread is None:
            self._notifyThread=Thread(
                target=self._notifyThreadLoop,daemon=useDaemonThreads)
            self._notifyThread.start()

    def stop(self):
        """
        Stop notifying

        NOTE: This will wait for all data to be
        read and notified, so you won't miss anything.
        """
        if self._notifyThread is not None:
            if self._notifyThread.is_alive():
                self._keepgoing=False
                self._notifyThread.join()
            self._notifyThread=None
