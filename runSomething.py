#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This is the future.  It is a generic, pluggable way to run things.
"""
import typing


class Runner:
    """
    A general-purpose something that can be run.
    """

    RUNNER_TYPE=None

    def __init__(self,name:str,commands:str,*args,**vaArgs):
        _=args
        self.name=name
        self.commands=commands
        for k,v in vaArgs.items():
            self.__dict__[k]=v


class RunSomething:
    """
    This is the future.  It is a generic, pluggable way to run things.
    """

    def __init__(self,*args,**vaArgs):
        _=args
        for k,v in vaArgs.items():
            self.__dict__[k]=v


def cmdline(args:typing.Iterable[str]):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    printhelp=False
    if not args:
        printhelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                arg=[a.strip() for a in arg.split('=',1)]
                if arg[0] in ['-h','--help']:
                    printhelp=True
                else:
                    print(('ERR: unknown argument "'+arg[0]+'"'))
            else:
                print(('ERR: unknown argument "'+arg+'"'))
    if printhelp:
        print('Usage:')
        print('  runSomething.py [options]')
        print('Options:')
        print('   NONE')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
