#!/usr/bin/env
# -*- coding: utf-8 -*-
"""
This program captures a window as an image.  It can even be a "hidden" window!
"""
import typing
from .find import findWindows


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    title=None
    filename='screenshot.png'
    printHelp=False
    if not args:
        printHelp=True
    else:
        for arg in args:
            if arg.startswith('-'):
                arg=[a.strip() for a in arg.split('=',1)]
                if arg[0] in ['-h','--help']:
                    printHelp=True
                elif arg[0]=='--title':
                    title=arg[1]
                elif arg[0]=='--out':
                    filename=arg[1]
                else:
                    print(('ERR: unknown argument "'+arg[0]+'"'))
            else:
                print(('ERR: unknown argument "'+arg+'"'))
    if printHelp:
        print('Usage:')
        print('   windowScreenshot.py [options]')
        print('Options:')
        print('   --title=[title] .... find windows with title')
        print('   --out=[filename] ... output filename to save screenshot(s)')
        return -1
    for window in findWindows(title):
        window.saveScreenshot(filename)
    return 0


if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
