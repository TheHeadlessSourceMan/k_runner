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


def runPythonFile(
    script:typing.Union[str,typing.Iterable[str]],
    args:typing.Optional[typing.Iterable[str]]=None,
    onOutputCB:typing.Optional[typing.Callable]=None,
    onErrorCB:typing.Optional[typing.Callable]=None,
    shell:bool=False
    )->int:
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
    if not isinstance(script,str):
        script=list(script)
        if len(script)>1:
            if args is not None:
                args=list(args)
                args.extend(script[1:])
            else:
                args=script[1:]
        script=script[0]
    script=os.path.abspath(script)
    oldArgs=sys.argv
    oldPath=sys.path
    oldStdout=sys.stdout
    oldStderr=sys.stderr
    errStringBuffer=io.StringIO()
    returncode=0
    has_err=False
    errIo=ErrIO(errStringBuffer)
    sys.argv=[script]
    sys.path=[]
    sys.path.extend(oldPath)
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
        returncode=eval( # pylint: disable=eval-used
            compile(open(script, "rb").read(),script,'exec'),
            _globals)
        #exec(compile(open(script,"rb").read(),script,'exec'),_globals)
    except Exception:
        exc_type,exc_value,exc_traceback=sys.exc_info()
        import traceback
        errIo.write('\n'.join(traceback.format_exception(
            exc_type,exc_value,exc_traceback)))
    if errIo.hasWritten:
        has_err=True
    sys.argv=oldArgs
    sys.path=oldPath
    sys.stdout=oldStdout
    sys.stderr=oldStderr
    return (has_err,errStringBuffer.getvalue(),returncode)


def cmdline(args:typing.Iterable[str]):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    args=list(args)
    printHelp=False
    if not args:
        printHelp=True
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
    if printHelp:
        print('Usage:')
        print('  runPythonFile some_script.py [parameters]')
        return -1
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
