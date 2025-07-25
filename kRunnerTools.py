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
from .dataRecievedCallbacks import ApplicationCallbacks
if os.name=='nt':
    from _kRunnerToolsWindows import Application
else:
    from _kRunnerToolsLinux import Application # type: ignore

# -------------- Api
def run(
    cmd:str,
    callbacks:typing.Optional[ApplicationCallbacks]=None,
    hideWindows:bool=False,
    priorityBoost:int=0,
    wDogOutput=None,
    wDogLifetime=None,
    shell:bool=False
    )->int:
    """
    Conveniently run a program using python.
    """
    return Application(shell).run(
        cmd,callbacks,hideWindows,
        priorityBoost,wDogOutput,wDogLifetime)

# -------------- Main entry point
def cmdline(args:typing.Iterable[str]):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    # Runs another program.
    # (Not useful for much besides testing this module.)
    print((Application(None).getShell()))
    _=args
    #run(args,hideWindows=True,wDogLifetime=10)


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
