import typing
import re as re
from paths import UrlCompatible,asUrl


def wrapTextSimple(s:str,indent:str='',width:int=80)->str:
    """
    Nieve wrap text (don't worry about breaking on spaces)
    """
    ret=[]
    while True:
        l=len(s)
        if l>width:
            ret.append(s[0:width])
            s=indent+s[width:]
        else:
            ret.append(s)
            break
    return '\n'.join(ret)


class Param:
    """
    deal with a single command line parameter

    TODO: there are other things this should be joined with
    """
    def __init__(self,name:str):
        self.name:str=name
        self.aliases:typing.List[str]=[]
        self.description:str=''
        self.equalValue:typing.Optional[str]=None
        self.equalValueOptional:bool=True

    def __repr__(self):
        return self.toHelpString()
    
    def _miniToHelpString(self)->str:
        ret=[self.name]
        if self.aliases:
            for a in self.aliases:
                ret.append(f', {a}')
        if self.equalValue is not None:
            if self.equalValueOptional:
                ret.append(f'[={self.equalValue}]')
            else:
                ret.append(f'={self.equalValue}')
        return ''.join(ret)

    def toHelpString(self,maxWidth:int=80,wrapIndent='    ',docSep:str='.',docSepMinLen:int=4)->str:
        """
        Create a new help string for this item
        """
        ret=[self._miniToHelpString()]
        if self.description:
            if docSep!=' ':
                ret.append(' ')
                ret.append(docSep*(docSepMinLen-len(ret[0])))
            else:
                ret.append(' '*(docSepMinLen-1-len(ret[0])))
            ret.append(' ')
            ret.append(self.description)
        s=''.join(ret)
        if maxWidth>0:
            s=wrapTextSimple(s,wrapIndent,maxWidth)
        return s

    def calculateFormatPWidth(self)->int:
        """
        Calculate the parameter width section
        for alignment purposes
        """
        return len(self._miniToHelpString())


class Params:
    def __init__(self):
        # NOTE: the same param may appear more than once in
        # the dict, eg. "-h" and "--help"
        self.params:typing.Dict[str,Param]={}

    def __repr__(self):
        return self.toHelpString()

    def toHelpString(self,maxWidth:int=80,docSep:str='.',docSepMinLen:int=4)->str:
        """
        Create a new help string for this item
        """
        values=set(self.params.values())
        for p in values:
            w=p.calculateFormatPWidth()
            if w>docSepMinLen:
                docSepMinLen=w
        ret=[]
        wrapIndent=' '*(docSepMinLen+2)
        for p in values:
            ret.append(p.toHelpString(maxWidth,wrapIndent,docSep,docSepMinLen))
        return '\n'.join(ret)


class CmdLineInfo:
    def __init__(self,executable:typing.Optional[UrlCompatible]=None,helpCommand:str='--help'):
        self.executable:typing.Optional[UrlCompatible]=None
        self.usage:str=''
        self.params:Params=Params()
        if executable is not None:
            self.extractHelpText(executable,helpCommand)

    def extractHelpText(self,executable:UrlCompatible,helpCommand:str='--help')->None:
        """
        extract help text from the executable output
        """
        import subprocess
        self.executable=executable
        cmd=[str(asUrl(executable))]
        if helpCommand:
            cmd.append(helpCommand)
        po=subprocess.Popen(cmd,shell=True,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        self.parseHelpText(out.strip().decode('utf-8',errors='ignore'))

    def parseHelpText(self,helpText:str)->None:
        """
        Parse a help text buffer
        """
        state=None
        lastLineBlank=True
        usage=[]
        currentIndent=''
        lastParam:typing.Optional[Param]=None
        self.params=Params()
        usageRe=re.compile(r'us(e|((e)?(age)))((\s*:\s*)|(\s+))(?P<contents>.*)',re.IGNORECASE)
        optionSplitRe=re.compile(r'(?P<params>(-[^\s,]+\s*,\s*)*(-[^\s,]+))[\s.,]+(?P<description>.*)',re.IGNORECASE)
        for line in helpText.split('\n'):
            line_s=line.lstrip()
            if line_s:
                if not usage:
                    m=usageRe.match(line_s)
                    if m is not None:
                        usage.append(str(m.group('contents')))
                        state='usage'
                elif line_s[0]=='-':
                    optionSplit=optionSplitRe.match(line_s)
                    if not optionSplit:
                        print(f'Skipping line "{line}"')
                        continue
                    state='params'
                    description=optionSplit.group('description')
                    paramNames=optionSplit.group('params').replace(',',' ').split()
                    lastParam=Param(paramNames[0])
                    if len(paramNames)>1:
                        lastParam.aliases=paramNames[1:]
                    lastParam.description=description
                    for p in paramNames:
                        self.params.params[p]=lastParam
                elif state=='usage':
                    usage.append(line)
                elif state=='params' and lastParam is not None:
                    lastParam.description=f'{lastParam.description} {line_s}'
                elif lastLineBlank:
                    # add end text to usage
                    state='usage'
                    usage.append('')
                    usage.append(line_s)
                currentIndent=line[-len(line_s)]
                lastLineBlank=False
            else:
                state=None # reset the state machine
                lastLineBlank=True
        self.usage='\n'.join(usage)

    def __repr__(self):
        ret=['Usage:',self.usage]
        if self.executable is not None:
            ret.insert(0,str(self.executable))
            ret.insert(1,'')
        ret.append('')
        ret.append(repr(self.params))
        return '\n'.join(ret)


cli=CmdLineInfo('cmd','/?')
#cli.parseHelpText('\n'.join(result))
print(cli)