#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This class will allow you to run a program and capture its input/output.
It is similar to the builtin Popen stuff,but much more versatile.

This will use pyev if available:  (TODO)
    http://code.google.com/p/pyev

Also,it will try to use system libraries if present.

Finally,if nothing else seems to be working,it'll revert back to the
old subprocess module.
"""
import typing
import os
import threading
import subprocess
import time
from .callbackDefs import ApplicationCallbacks

try:
    import signal
    import pyev
    hasPyEv=True
except:
    hasPyEv=False

try:
    import pywintypes
    import win32process
    import win32pipe
    import win32file
    import win32con
    import win32gui
    import win32event
    import win32security
    #import msvcrt
    import win32api
    hasWindowsStuff=True
except ImportError:
    hasWindowsStuff=False


# -------------- Api
def run(cmd:str,callbacks:ApplicationCallbacks=None,hideWindows:bool=False,priorityBoost:int=0,
    wDogOutput=None,wDogLifetime=None,shell:bool=False):
    """
    Conveniently run a program using python.
    """
    return Application(shell).run(cmd,callbacks,hideWindows,priorityBoost,wDogOutput,wDogLifetime)


def getWindowsByPid(pid:int)->typing.List:
    """
    Get handles to all windows belonging to a certain process
    """
    return []


def hideAllWindows(pid:int,hide:bool=True):
    """
    Hide (or show) all windows belonging to a certain process
    """
    pass


def processExists(pid:int):
    """
    Determine if a process exists.
    """
    return False


def killProcess(pid:int):
    """
    End a process.  Starts out requesting a friendly shutdown but gradually
    gets more violent.
    """
    # give it a chance to go down peacefully
    os.kill(pid,signal.SIGTERM)
    for _ in range(100):
        if not processExists(pid):
            return
        time.sleep(0.010)
    # nuke that sob!
    os.kill(pid,-9)


class Application:
    """
    Wrapper class for a running application.
    """

    def __init__(self,runInShell:bool=True,runInShellCommandFlag:str='-c'):
        """
        If runInShell=True,then use the default shell.  If it is a string,use the
        default shell.
        """
        if not runInShell:
            runInShell=None
        self.runInShell=runInShell
        self.runInShellCommandFlag=runInShellCommandFlag
        self.returnCode=None
        # watchdog management
        self.wDogTouch=False
        self.onOutputCB=None
        self.onErrorCB=None
        self.dDogOutput=None
        self.wDogLifetime=None
        self.hideWindows=False
        self.wDogOutput=None
        self.returncode=None
        self.process=None
        self._imgData=None
        self._threadsKeepGoing=False
        self.granularity=0.010
        self.lifetimeCounter=0.0
        self.outputCounter=0.0
        self.wDogExitCode=-1077

    def sendIn(self,data:str):
        """
        Send something to the program's standard input
        """
        self.process.stdin.write(data)

    def getShell(self)->str:
        """
        This returns the current shell command (regardless of whether or not it would be used)
        """
        if self.runInShell is None or self.runInShell:
            out,err=subprocess.Popen('echo $SHELL',stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True).communicate()
            if err:
                out='/bin/sh'
                print(('ERR: Cannot find shell.  Defaulting to '+out+'.'))
                print(('\t'+'\t\n'.join(err.split('\n'))))
            return out.strip()
        return str(self.runInShell)

    def __pipeFileIO(self):
        """
        This is something I was fiddling with to speed up file i/o.
        Rather than writing to disk,it reads/writes to named pipes.

        Unfortunately,it has problems.  Namely,if the target program does
        not use the proper windows api for opening files,it will not understand
        unc paths and barf all over the place.
        """
        self._imgData=None
        self._threadsKeepGoing=True
        # a named pipe to send input to OpenSCAD
        openscadInputFilename=r'\\.\pipe\openscadInputPipe'
        openscadInputPipe=win32pipe.CreateNamedPipe(
                openscadInputFilename,# name
                win32con.PIPE_ACCESS_OUTBOUND | win32con.FILE_FLAG_OVERLAPPED,# open mode
                win32con.PIPE_TYPE_BYTE,# pipe mode
                1,# max instances
                len(self.openscadReplacement),# out buffer size
                0,# in buffer size
                0,# timeout
                None)
        overlapped=pywintypes.OVERLAPPED()
        overlapped.hEvent=win32event.CreateEvent(None,1,0,None)
        win32pipe.ConnectNamedPipe(openscadInputPipe,overlapped)
        def _writer():
            while self._threadsKeepGoing:
                try:
                    ret=win32file.WriteFile(openscadInputPipe,self.openscadReplacement)
                    print(ret)
                    return
                except Exception as e:
                    if hasattr(e,'winerror') and e.winerror==536:
                        pass
                    elif e.winerror==233: # process disconnected
                        break
                    else:
                        raise e
                time.sleep(0.5)
            print('Write thread exited gracefully')
        writeThread=threading.Thread(target=_writer)
        writeThread.start()
        # a named pipe to get output from OpenSCAD
        openscadOutputFilename=r'\\.\pipe\openscadOutputPipe.png'
        openscadOutputPipe=win32pipe.CreateNamedPipe(
            openscadOutputFilename,# name
            win32pipe.PIPE_ACCESS_INBOUND,# open mode
            win32pipe.PIPE_TYPE_BYTE,# pipe mode
            1,# max instances
            0,# out buffer size
            2097152,# in buffer size
            0,# timeout
            None)
        def _reader():
            while self._threadsKeepGoing:
                try:
                    errno,data=win32file.ReadFile(openscadOutputPipe,1024)
                    print(('Read ',len(data),'image bytes'))
                    self._imgData=data
                except Exception as e:
                    if hasattr(e,'winerror') and e.winerror==536:
                        pass
                    else:
                        raise e
                time.sleep(0.5)
            print('Read thread exited gracefully')
        readThread=threading.Thread(target=_reader)
        readThread.start()
        # this is a sample command line to run openscad
        # unfortunately,openscad uses the wrong file open,so this does not work
        cmd=self.openscadProgram+' -o '+openscadOutputFilename+' '+openscadInputFilename
        print(('Running: ',cmd))
        po=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        print(out)
        # shut down pipes and such
        self._threadsKeepGoing=False
        win32pipe.DisconnectNamedPipe(openscadInputPipe)
        return self._imgData

    def run(self,cmd:str,callbacks=None,hideWindows:bool=False,
        priorityBoost:int=0,wDogOutput=None,wDogLifetime=None)->int:
        """
        runs a program (via the standard POSIX API)
        """
        if callbacks is None:
            callbacks=ApplicationCallbacks()
        if isinstance(cmd,list):
            cmd=[cmd]
        if self.runInShell is not None:
            cmd.insert(0,self.runInShellCommandFlag)
            cmd.insert(0,self.getShell())
        if callbacks.stdoutLine is None:
            def onOutput(app,out):
                """
                stdout callback
                """
                print(out)
            onOutputCB=onOutput
        if callbacks.stderrLine is None:
            def onError(app,err):
                """
                stderr callback
                """
                print(("[ERR]",err))
                # make sure we get all the error message then quit
                app.wDogOutput=None
                app.lifetimeCounter=0.0
                app.wDogLifetime=0.100
            onErrorCB=onError
        self.callbacks=callbacks
        self.dDogOutput=wDogOutput
        self.wDogLifetime=wDogLifetime
        self.hideWindows=hideWindows
        self.wDogOutput=wDogOutput
        result=0
        try:
            # TODO: This currently does not allow parameters! *unless* you enable
            # shell=true,which causes un-killabiliy problems
            self.process=subprocess.Popen(
                cmd,
                bufsize=1,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                # Uncommenting the next parameter can solve some running problems,but you'll
                # no longer be able to kill the process. (Personally,it's just not worth it!)
                #shell=True
                )
        except OSError as e:
            print(('ERR: Unable to execute "'+cmd+'" because:'))
            print(('\t',e))
            return -1
        # TODO: This next line is incorrect.  os.nice can only change the current process,not an arbitrary pid
        #os.nice(self.process.pid,priorityBoost)
        # The watchdog
        threading.Thread(target=self._wDogThread).start()
        # The stdout loop
        threading.Thread(target=self._stdoutReadThread).start()
        # The stderr loop
        result=None
        while result is None and self.returnCode is None:
            line=self.process.stderr.readline()
            if line is not None:
                self.process.wDogTouch=True
                while line and (line[-1]=='\n' or line[-1]=='\r'):
                    line=line[0:-1]
                    self.onErrorCB(self,line)
            result=self.process.poll()
        if self.returnCode is None:
            self.returnCode=result
        return self.returnCode

    def _stdoutReadThread(self):
        """
        Thread to read stdout of a (POSIX) process
        """
        result=None
        while result is None and self.returnCode is None:
            line=self.process.stdout.readline()
            if line is not None:
                self.wDogTouch=True
                while line and (line[-1]=='\n' or line[-1]=='\r'):
                    line=line[0:-1]
                    toIn=self.onOutputCB(self,line)
            result=self.process.poll()

    def _wDogThread(self):
        """
        Thread to monitor a (POSIX) process for lockups
        """
        while self.process.poll() is None and self.returnCode is None:
            if self.hideWindows:
                # Sadly,we can't specify window visibility on startup (yet). We'll
                # just have to watch for new windows and hide them manually.
                hideAllWindows(self.process.pid)
            if self.wDogTouch:
                self.wDogTouch=False
                self.outputCounter=0.0
            if self.wDogOutput is not None and self.outputCounter>self.wDogOutput:
                killProcess(self.process.pid)
                print(("Watchdog output timer fired (",self.outputCounter,self.wDogOutput,")"))
                self.returncode=self.wDogExitCode
                break
            if self.wDogLifetime is not None and self.lifetimeCounter>self.wDogLifetime:
                killProcess(self.process.pid)
                print(("Watchdog lifetime timer fired (",self.lifetimeCounter,self.wDogLifetime,")"))
                self.returncode=self.wDogExitCode
                break
            self.lifetimeCounter=self.lifetimeCounter+self.granularity
            self.outputCounter=self.outputCounter+self.granularity
            time.sleep(self.granularity)


# -------------- Windows
if hasWindowsStuff:
    def getWindowsByPid(pid:int)->typing.Iterable[int]:
        """
        Get handles to all windows belonging to a certain process
        """
        hWnds=[]
        def onFound(hWnd,windows):
            """
            Windows needs an enumerator callback
            """
            _,wndPid=win32process.GetWindowThreadProcessId(hWnd)
            if wndPid==pid:
                hWnds.append(hWnd)
            return True
        win32gui.EnumWindows(onFound,hWnds)
        return hWnds


    def hideAllWindows(pid:int,hide:bool=True)->None:
        """
        Hide (or show) all windows belonging to a certain process
        """
        wnds=getWindowsByPid(pid)
        if hide:
            state=win32con.SW_HIDE
        else:
            state=win32con.SW_SHOWNA
        for wnd in wnds:
            win32gui.ShowWindow(wnd,state)


    def processExists(pid:int)->bool:
        """
        Determine if a process exists.

        TODO:
        """
        return True


    def killProcess(pid:int)->None:
        """
        End a process.  Starts out requesting a friendly shutdown but gradually
        gets more violent.
        """
        # give it a chance to go down peacefully
        hWnds=getWindowsByPid(pid)
        for hWnd in hWnds:
            win32gui.PostMessage(hWnd,win32con.WM_CLOSE)
        for _ in range(100):
            if not processExists(pid):
                return
            time.sleep(0.010)
        # a little bit meaner
        for hWnd in hWnds:
            win32gui.PostMessage(hWnd,win32con.WM_QUIT)
        for _ in range(100):
            if not processExists(pid):
                return
            time.sleep(0.010)
        # nuke that sob!
        try:
            handle=win32api.OpenProcess(win32con.PROCESS_TERMINATE,0,pid)
            if handle:
                win32api.TerminateProcess(handle,0)
                win32api.CloseHandle(handle)
        except:
            pass


    class Application:
        """
        Wrapper class for a running application.
        """

        def __init__(self,runInShell:bool=False,runInShellCommandFlag:str='/C'):
            """
            If runInShell=True,then use the default shell.  If it is a string,use the
            default shell.
            """
            if not runInShell:
                runInShell=None
            self.runInShell=runInShell
            self.runInShellCommandFlag=runInShellCommandFlag
            self.returnCode=None
            # watchdog management
            self.wDogTouch=False
            self.callbacks=None
            self.dDogOutput=None
            self.wDogLifetime=None
            self.wDogOutput=None
            self.hideWindows=None
            self.dDogOutput=None
            self.returncode=None
            self.process=None
            self.fIn=None
            self.fOut=None
            self.fErr=None
            self.pid=None
            self.granularity=0.010
            self.lifetimeCounter=0.0
            self.outputCounter=0.0
            self.wDogExitCode=-1077

        def sendIn(self,data:str)->None:
            """
            Send something to the program's standard input
            """
            self.process.stdin.write(data)

        def getShell(self)->str:
            """
            This returns the current shell command (regardless of whether or not it would be used)
            """
            if self.runInShell is None or self.runInShell:
                return 'command'
            return str(self.runInShell)

        def run(self,cmd:str,callbacks:ApplicationCallbacks=None,hideWindows:bool=False,
            priorityBoost:int=0,wDogOutput=None,wDogLifetime=None)->int:
            """
            runs a program (via the windows API)

            NOTE: The reason we use this instead of subprocess.Popen is because
            we need more control like hiding the window and boosting priority.

            See http://docs.activestate.com/activepython/2.4/pywin32/win32process__CreateProcess_meth.html
            """
            if isinstance(cmd,list):
                cmd=' '.join(cmd)
            if self.runInShell is not None:
                cmd=self.runInShellCommandFlag+' '+cmd
                cmd=self.getShell()+' '+cmd
            if callbacks.stdoutLine:
                def onOutput(app,out):
                    """
                    callback for stdout
                    """
                    print(out)
                onOutputCB=onOutput
            if callbacks.stderrLine:
                def onError(app,err):
                    """
                    callback for stderr
                    """
                    print(("[ERR]",err))
                    # make sure we get all the error message then quit
                    app.wDogOutput=None
                    app.lifetimeCounter=0.0
                    app.wDogLifetime=0.100
                onErrorCB=onError
            self.onOutputCB=onOutputCB
            self.onErrorCB=onErrorCB
            self.dDogOutput=wDogOutput
            self.wDogLifetime=wDogLifetime
            self.hideWindows=False
            # Enable this if you want to watch for and hide any child windows
            #self.hideWindows=hideWindows
            self.wDogOutput=wDogOutput
            # create some pipes to handle I/O
            security=win32security.SECURITY_ATTRIBUTES()
            security.bInheritHandle=1
            hStdin_r,hStdin_w=win32pipe.CreatePipe(security,0)
            hStdout_r,hStdout_w=win32pipe.CreatePipe(security,0)
            hStderr_r,hStderr_w=win32pipe.CreatePipe(security,0)
            # setup the startup parameters to our liking
            startInfo=win32process.STARTUPINFO()
            startInfo.hStdInput=hStdin_r
            startInfo.hStdOutput=hStdout_w
            startInfo.hStdError=hStderr_w
            startInfo.dwFlags=win32process.STARTF_USESTDHANDLES
            if hideWindows:
                startInfo.dwFlags=startInfo.dwFlags|win32process.STARTF_USESHOWWINDOW
                startInfo.wShowWindow=startInfo.wShowWindow|win32con.SW_HIDE
            if priorityBoost<=-1:
                dwFlags=win32process.BELOW_NORMAL_PRIORITY_CLASS
            elif priorityBoost==0:
                dwFlags=win32process.NORMAL_PRIORITY_CLASS
            elif priorityBoost==1:
                dwFlags=win32process.ABOVE_NORMAL_PRIORITY_CLASS
            elif priorityBoost==2:
                dwFlags=win32process.HIGH_PRIORITY_CLASS
            elif priorityBoost==3:
                dwFlags=win32process.REALTIME_PRIORITY_CLASS
            def MakeHandleLessStupid(handle):
                """
                Clean up handle access for async io
                """
                pid=win32api.GetCurrentProcess()
                newHandle=win32api.DuplicateHandle(pid,handle,pid,0,0,win32con.DUPLICATE_SAME_ACCESS)
                win32file.CloseHandle(handle)
                return newHandle
            hStdin_w=MakeHandleLessStupid(hStdin_w)
            hStderr_r=MakeHandleLessStupid(hStderr_r)
            hStdout_r=MakeHandleLessStupid(hStdout_r)
            # letter rip!
            hProcess,hThread,dwProcessId,dwThreadId=win32process.CreateProcess(
                None,# a name for it
                cmd,# command line
                None,# security crap
                None,# ditto
                1,# whether or not handles are inherited
                dwFlags,# startup flags
                None,# environment variables (dictionary)
                None,# current working directory
                startInfo) # the startup info
            # get rid of stuff that we don't care about and save stuff we do
            win32file.CloseHandle(hStderr_w)
            win32file.CloseHandle(hStdout_w)
            win32file.CloseHandle(hStdin_r)
            hThread.Close()
            self.fIn=hStdin_w
            self.fOut=hStdout_r
            self.fErr=hStderr_r
            self.pid=dwProcessId
            # The watchdog
            threading.Thread(target=self._wDogThread).start()
            # The stdout loop
            threading.Thread(target=self._stdoutReadThread).start()
            # The stderr loop
            try:
                err=""
                while True:
                    n,c=win32file.ReadFile(self.fErr,1)
                    if n!=1:
                        break
                    elif c=="\n":
                        self.wDogTouch=True
                        err=self.onErrorCB(self,err)
                        if err is not None and err:
                            win32file.Write(self.fErr,err)
                        err=""
                    elif c=="\r":
                        pass
                    else:
                        err=err+c
            except win32api.error:
                # This is normal.  This happens when the pipe is shut down cuz the child process has terminated.
                pass
            if self.returnCode is None:
                self.returnCode=win32process.GetExitCodeProcess(hProcess)
            hProcess.close()
            return self.returnCode

        def _stdoutReadThread(self):
            """
            Thread to read stdout of a (windows) process
            """
            try:
                out=""
                while True:
                    n,c=win32file.ReadFile(self.fErr,1)
                    if n!=1:
                        break
                    elif c=="\n":
                        self.wDogTouch=True
                        out=self.onOutputCB(self,out)
                        if out is not None and out:
                            win32file.Write(self.fIn,out)
                        out=""
                    elif c=="\r":
                        pass
                    else:
                        out=out+c
            except win32api.error:
                # This is normal.  This happens when the pipe is shut down cuz the child process has terminated.
                pass

        def _wDogThread(self):
            """
            Thread to monitor a (windows) process for lockups

            NOTE: I'm pretty sure we can also try and force a windows program to terminate
            by closing its STDIN.
            """
            try:
                while self.returnCode is None:
                    if self.hideWindows:
                        hideAllWindows(self.pid)
                    if self.wDogTouch:
                        self.wDogTouch=False
                        self.outputCounter=0.0
                    if self.wDogOutput is not None and self.outputCounter>self.wDogOutput:
                        print(("Watchdog output timer fired (",self.outputCounter,self.wDogOutput,")"))
                        self.returncode=self.wDogExitCode
                        killProcess(self.pid)
                        break
                    if self.wDogLifetime is not None and self.lifetimeCounter>self.wDogLifetime:
                        print(("Watchdog lifetime timer fired (",self.lifetimeCounter,self.wDogLifetime,")"))
                        self.returncode=self.wDogExitCode
                        killProcess(self.pid)
                        break
                    self.lifetimeCounter=self.lifetimeCounter+self.granularity
                    self.outputCounter=self.outputCounter+self.granularity
                    time.sleep(self.granularity)
            except win32api.error:
                # This is normal.  This happens when the pipe is shut down cuz the child process has terminated.
                pass


# -------------- Main entry point
def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    # Runs another program.
    # (Not useful for much besides testing this module.)
    print((Application(None).getShell()))
    #run(args,hideWindows=True,wDogLifetime=10)


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])