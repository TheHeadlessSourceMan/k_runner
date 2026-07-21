"""
Tools for working with command line strings
"""
import typing


def argvToString(argv:typing.Iterable[str])->str:
    """
    convert a list of arguments into a string
    does helpful things like adding quotes
    """
    ret:typing.List[str]=[]
    for arg in argv:
        if arg.find(' ')>=0 or arg.find('"')>=1:
            arg=arg.replace('\\','\\\\').replace('"','\\"')
            arg=f'"{arg}"'
        ret.append(arg)
    return ' '.join(ret)


def commandlineSplit(cmdline:typing.Union[str,typing.Iterable[str]]
    )->typing.Tuple[str,typing.List[str]]:
    """
    split a command line into a cmd,params[]
    (unquoting as necessary)
    """
    cmd:str=''
    params:typing.List[str]=[]
    if not isinstance(cmdline,str):
        first=True
        for c in params:
            if first:
                cmd=c
                first=False
            else:
                params.append(c) # pylint: disable=modified-iterating-list
        return (cmd,params)
    inQuot=''
    delimitNextQuote=False
    building:typing.List[str]=[]
    for c in cmdline:
        if inQuot:
            if c=='\\':
                if delimitNextQuote:
                    building.append('\\')
                else:
                    delimitNextQuote=True
            elif c==inQuot:
                if delimitNextQuote:
                    building.append(c)
                    delimitNextQuote=False
                else:
                    inQuot=''
            else:
                if delimitNextQuote:
                    building.append('\\')
                    delimitNextQuote=False
                building.append(c)
        else:
            if c in ('"',"'"):
                if delimitNextQuote:
                    building.append(c)
                    delimitNextQuote=False
                else:
                    inQuot=c
            elif c in (' ','\t','\r','\n'):
                if delimitNextQuote:
                    building.append('\\')
                    delimitNextQuote=False
                if building:
                    if not cmd:
                        cmd=''.join(building)
                    else:
                        params.append(''.join(building))
                    building=[]
            elif c=='\\':
                if delimitNextQuote:
                    building.append('\\')
                else:
                    delimitNextQuote=True
            else:
                if delimitNextQuote:
                    building.append('\\')
                    delimitNextQuote=False
                building.append(c)
    if building:
        if not cmd:
            cmd=''.join(building)
        else:
            params.append(''.join(building))
    return (cmd,params)
