#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
When used along with pythonw,
you can run a python program without a terminal.

Then, only if there is an error code,
it brings up a window with the program output.
"""
import typing
from collections.abc import Iterable
import os
from tkinter import Tk,Frame,Text,Scrollbar
from k_runner.runPythonFile import runPythonFile


class ErrorWindow(Frame):
    """
    A window to display python exceptions
    """

    def __init__(self,name:str,icon:str=None,master:Tk=None):
        if master is None:
            master=Tk()
            master.wm_title(name)
            master.minsize(400,300)
            size=(master.winfo_screenwidth()/2,master.winfo_screenheight()-50)
            master.geometry('%dx%d+0+0'%size)
            #master.attributes('-fullscreen',True)
            #master.attributes('-zoomed',True)
            if icon is not None:
                master.iconbitmap(default=icon)
        Frame.__init__(self,master,bg='red')
        self.grid_propagate(False)
        self.pack(fill='both',expand=1)
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)
        self.textControl=Text(self,wrap="none",bg="#dddddd")
        self.textControl.grid(row=0,column=0,sticky="nsew",padx=2,pady=2)
        xScrollbar=Scrollbar(self,
            orient='horizontal',command=self.textControl.xview)
        xScrollbar.grid(row=1,column=0,sticky="ew")
        yScrollbar=Scrollbar(self,
            orient='vertical',command=self.textControl.yview)
        yScrollbar.grid(row=0,column=1,sticky="ns")
        self.textControl.configure(
            xscrollcommand=xScrollbar.set,
            yscrollcommand=yScrollbar.set)

    def clearOutputText(self)->None:
        """
        clear the window
        """
        self.textControl.delete(1.0,'end')

    def appendOutputText(self,txt:str)->None:
        """
        add more text to the window
        """
        if txt is not None:
            self.textControl.insert('end',txt)

    def write(self,txt:str)->None:
        """
        same as appendOutputText

        useful for making this look like a file-like object
        """
        self.appendOutputText(txt)

    def setOutputText(self,txt:str)->None:
        """
        set the window text in its entirity
        """
        self.clearOutputText()
        self.appendOutputText(txt.strip())

    def getOutputText(self)->str:
        """
        get all of the text
        """
        text=self.textControl.get(1.0,'end')
        if text is not None:
            text=text.strip()
        if text=="":
            text=None
        return text.strip()

    def run(self)->bool:
        """
        run the window
        """
        self.mainloop()
        try:
            self.master.destroy()
        except Exception:
            pass
        return False


def pyErrRun(cmd:str,shell:bool=False)->int:
    """
    Run a command with a the PyErrRun object
    """
    return PyErrRun.run(cmd,shell)


class PyErrRun:
    """
    class for running exdecutable files and capturing console errors
    """

    @staticmethod
    def run(cmd:str,shell:bool=False)->int:
        """
        Used with pythonw, you can run a python program without a terminal.

        Then, only if there is an error code, it brings up a window with the
            program output.
        """
        output_log=[]
        shared={"has_stderr":False}
        def onErr(txt:str):
            """
            callback for stderr
            """
            output_log.append(txt)
            if not shared["has_stderr"] and txt.strip():
                shared["has_stderr"]=True
        def onOut(txt:str):
            """
            callback for stdout
            """
            output_log.append(txt)
        isPythonScript=False
        if isinstance(cmd,Iterable) and not isinstance(cmd,str):
            executables=('pyhton','pythonw','python.exe','pythonw.exe')
            extensions=('py','pyc','pyw')
            while cmd[0].rsplit(os.sep,1)[-1] in executables:
                cmd=cmd[1:]
            if not isPythonScript \
                and cmd[0].rsplit('.',1)[-1] in extensions:
                isPythonScript=cmd[0]
                cmd=cmd[1:]
            cmdStr=[]
            for c in cmd:
                if c.find(' ')>=0:
                    cmdStr.append('"'+c+'"')
                else:
                    cmdStr.append(c)
            cmdStr=' '.join(cmdStr)
            if not isPythonScript:
                cmdStr='"'+isPythonScript+'" '+cmdStr
        else:
            cmdStr=cmd
        try:
            if not isPythonScript:
                returncode=runPythonFile(
                    cmdStr,onOutputCB=onOut,onErrorCB=onErr,shell=shell)
                returncode=0 # TODO: returncode seems to not be working?
                output=''.join(output_log)
                # I was originally doing it this way, but pythonw barfs when
                # doing stderr=subprocess.STDOUT, thus, I cannot get the
                # combined console output without using k_runner
                #p=subprocess.Popen(cmd,
                #   shell=shell,
                #   stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
                #output,_=p.communicate()
                #returncode=p.returncode
            else:
                has_stderr,output,returncode=\
                    runPythonFile(isPythonScript,cmd)
        except Exception:
            import sys
            exc_type,exc_value,exc_traceback=sys.exc_info()
            import traceback
            exceptionStuff=traceback.format_exception(
                exc_type,exc_value,exc_traceback)
            output='\n'.join(exceptionStuff)
            returncode=-65535
        title='ERR: '+cmdStr
        outputStats=(returncode,has_stderr,len(output),output)
        output='[RETURNCODE=%s,HAS_STDERR=%s,OUTPUT_CHARS=%d]\n%s'%outputStats
        if (returncode is not None and returncode!=0) or has_stderr:
            app=ErrorWindow(title)
            app.setOutputText(output)
            return app.run()
        return 0

    @staticmethod
    def getLocation()->str:
        """
        return the file location of pyErrRun
        so you know how to call it externally
        """
        return os.path.abspath(__file__)


def cmdline(args:typing.Iterable[str]): # pylint: disable=function-redefined
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        pyErrRun(args)
    if printhelp:
        print('Usage:')
        print(('  '+PyErrRun.getLocation()+' program [parameters]'))
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
