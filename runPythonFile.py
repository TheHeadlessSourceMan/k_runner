#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This is a tool to run a python file and capture the output

Generally this is unneeded, but sometimes you want to keep
each kid in their own sandbox.
"""
import typing
import os


class ErrIO:
    """
    Simply a write pass-though file-like object
    It also watches to see if any non-whitespace bytes have been written
    """
    def __init__(self,mirrorToFile:typing.IO):
        self.mirrorToFile=mirrorToFile
        self.hasWritten=False

    def write(self,data:str):
        """
        write some data to the error io buffer
        """
        self.mirrorToFile.write(data)
        if not self.hasWritten and data.strip():
            self.hasWritten=True


def runPythonFile(script:str,args:typing.Iterable[str]=None):
    """
    runs a python script

    args - an array of arguments

    returns (has_err,outputString,returncode)

    NOTE: this is similar (and, indeed, uses) execfile().
    What it adds is:
        1) Standard output/err capture
        2) Ability to pass arguments
        3) detect if stderr has been written to
        4) inclusion of target script location in the pythonpath
    """
    import io
    import sys
    script=os.path.abspath(script)
    oldargs=sys.argv
    oldpath=sys.path
    oldstdout=sys.stdout
    oldstderr=sys.stderr
    errStringBuffer=io.StringIO()
    returncode=0
    has_err=False
    errIo=ErrIO(errStringBuffer)
    sys.argv=[script]
    sys.path=[]
    sys.path.extend(oldpath)
    scriptPath=script.rsplit(os.sep,1)[0]
    sys.path.append(scriptPath)
    _globals=dict(globals())
    _globals['__name__']='__main__'
    _globals['__file__']=script
    #if os.path.isfile(scriptPath+os.sep+'__init__.py'):
    #    _globals['__package__']=scriptPath.rsplit(os.sep,1)[-1]
    if args is not None and args:
        sys.argv.extend(args)
    try:
        sys.stderr=errIo
        sys.stdout=errStringBuffer
        returncode=exec(compile(open(script, "rb").read(), script, 'exec'),_globals)
        #exec(compile(open(script,"rb").read(),script,'exec'),_globals)
    except Exception:
        exc_type,exc_value,exc_traceback=sys.exc_info()
        import traceback
        errIo.write('\n'.join(traceback.format_exception(exc_type,exc_value,exc_traceback)))
    if errIo.hasWritten:
        has_err=True
    sys.argv=oldargs
    sys.path=oldpath
    sys.stdout=oldstdout
    sys.stderr=oldstderr
    return (has_err,errStringBuffer.getvalue(),returncode)


def cmdline(args:typing.Iterable[str]):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        print(' '.join(args))
        pythonFile=args[0]
        params=None
        if len(args)>1:
            params=args[1:]
        has_err,outputString,returncode=runPythonFile(pythonFile,params)
        print('has error=',has_err)
        print('return code=',returncode)
        print('-----------------------')
        print(outputString)
    if printhelp:
        print('Usage:')
        print('  runPythonFile some_script.py [parameters]')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))