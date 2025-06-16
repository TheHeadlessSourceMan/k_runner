#!/usr/bin/python
"""
A tool to get information about an app from its help system.

Supports:
    * help from the command line (e.g. myapp --help)
    * the installed Linux man pages
    * [in progress] the windows help system
"""
import typing
import re
import subprocess


class CommandLineOption:
    """
    A description of a single command line option
    """

    def __init__(self,
        options:typing.Union[str,typing.Iterable[str]],
        name:typing.Optional[str]=None,
        description:str='',
        paramsAfter:typing.Optional[typing.Iterable[str]]=None):
        """
        If name is not given, it will attempt to use the longest option name.
        """
        if isinstance(options,str):
            options=[options]
        self.options=options
        if len(paramsAfter)>1 and paramsAfter[0]=='=':
            tagon='='+(' '.join(paramsAfter[1:]))
            self.options=[o+tagon for o in self.options]
        if name is None:
            name=''
            for o in options:
                o=o.split('=',1)[0].split('[',1)[0]
                if len(o)>len(name):
                    name=o
            if len(name)>0:
                while name[0]=='-':
                    if len(name)>1:
                        name=name[1:]
                    else:
                        break
            name=name.replace('-','_')
        self.name=name
        self.description=description
        self.paramsAfter=paramsAfter

    def getHelp(self)->str:
        """
        Get a basic help string for this option
        """
        return self.name+' - '+self.description

    def __repr__(self)->str:
        return self.getHelp()


class HelpSystemEntry:
    """
    A tool to get information about an app from its help system.

    Supports:
        * help from the command line (e.g. myapp --help)
        * the installed Linux man pages
        * [in progress] the windows help system

    TODO: This currently gets all the help via getCommandLineOptions
        because that's what was written first. This is a little
        non-intuitive and should be changed.
    """
    def __init__(self,app:typing.Optional[str]=None):
        self.app=app
        self.name=app
        self.description=''
        self.commandLineOptions=[]
        self.helpText=None
        self.helpHtml=None

    def getHelpHtml(self)->str:
        """
        Gets the help as html, fetching it from the help system if necessary.
        """
        if self.helpHtml is None:
            if self.helpText is None:
                self.getCommandLineOptions()
            if self.helpHtml is None:
                # appears redundant, but is here in case
                # getCommandLineOptions returned some html
                title='Help: '+self.__toHtml(self.name)
                self.helpHtml='<html><head><title>'+title+'</title></head><body><h1>'+title+'</h1><div style="margin-left:2cm;font-family:\'Courier New\',monospace;">'+self.__toHtml(self.helpText)+'</div></body></html>' # noqa: E501 # pylint: disable = line-too-long
        return self.helpHtml

    def getHelpChm(self)->str:
        """
        Gets the help as windows chm file, fetching it from the
        help system if necessary.

        TODO: Work in progress

        Requires:
            python-chm - most systems have a package, but you can also
            get it from the homepage:
                http://gnochm.sourceforge.net/pychm.html
        """
        return '' # TODO: implement this

    def getHelpText(self)->str:
        """
        Gets the help as plain text, fetching it from the
        help system if necessary.
        """
        if self.helpText is None:
            if self.helpHtml is None:
                self.getCommandLineOptions()
            if self.helpText is None:
                # appears redundant, but is here in case
                # getCommandLineOptions returned some text
                self.helpText=self.__unHtml(self.helpHtml,preformatted=True)
        return self.helpText

    def __repr__(self):
        return self.getHelpText()

    def getCommandLineOptions(self,
        urlBufferOrFile:typing.Union[None]=None
        )->typing.Iterable[CommandLineOption]:
        """
        Tries to get the command line options for a program any way it can.

        If urlBufferOrFile it tries to get the command line options for
        a program from the given source.
        Otherwise, it will try to automatically get information
        about the program.

        This source can be either html or plaintext and you can pass in
        a filename, url, or string containing the data.
        You can also specify "man" or "[app_name][ help_parameter]" to
        specifically query the manpage or command itsself.

        Since there are a lot of different ways the source could be formatted,
        this may or may not always work.

        Manpages saved as HTML are the most surefire bet.
        """
        if urlBufferOrFile is not None and urlBufferOrFile:
            if urlBufferOrFile[0]=='-':
                # this looks like a command line parameter, so assume
                # they meant to run the app with this
                self.__getCommandLineOptionsFromAppHelp(urlBufferOrFile)
                return
            elif urlBufferOrFile=='man':
                # get from the man page
                self.__getCommandLineOptionsFromMan()
                return
            elif urlBufferOrFile.split(' ',1)[0]==self.app:
                # get from the app itsself
                urlBufferOrFile=urlBufferOrFile.split(' ',1)
                if len(urlBufferOrFile)>1:
                    self.__getCommandLineOptionsFromAppHelp(urlBufferOrFile[1])
                else:
                    raise Exception(
                        'Nothing to get the command line arguments of')
                return
            elif urlBufferOrFile.find('\n') or urlBufferOrFile.find('<'):
                # buffer
                textBuffer=urlBufferOrFile
            elif urlBufferOrFile.find('://')>=0:
                # url or file
                from paths import Url
                f=Url(urlBufferOrFile)
                textBuffer=f.read()
                f.close()
            textBuffer=textBuffer.strip()
            if textBuffer[0]=='<':
                self.__getCommandLineOptionsFromHtml(textBuffer)
            else:
                self.__getCommandLineOptionsFromText(textBuffer)
        else:
            # Try and find the info automatically
            if len(self.commandLineOptions)<1:
                self.__getCommandLineOptionsFromMan()
            if len(self.commandLineOptions)<1:
                self.__getCommandLineOptionsFromAppHelp('/?') # windows style
            if len(self.commandLineOptions)<1:
                self.__getCommandLineOptionsFromAppHelp('--help') # this is fairly common # noqa: E501 # pylint: disable = line-too-long
            if len(self.commandLineOptions)<1:
                self.__getCommandLineOptionsFromAppHelp('-h') # now we're just getting desperate # noqa: E501 # pylint: disable = line-too-long
        return self.commandLineOptions

    def __getCommandLineOptionsFromText(self,
        text:str
        )->typing.Iterable[CommandLineOption]:
        """
        this reges returns:
            (options separated by space and/or comma)
            (parameters)
            (multiline description)
        it could maybe use some cleanup, but works pretty well overall
        """
        self.helpText=text
        regex=r"""^((?:[,\s]*[-/]{1,2}[^\s]*)+)(\s.*?)[\s\.:=>]{2,}(.*?)(?:(?=^\s*[-/])|\z)""" # noqa: E501 # pylint: disable = line-too-long
        regex=re.compile(regex,re.MULTILINE|re.DOTALL)
        for m in regex.finditer(text):
            options=str(m.group(1)).replace(',',' ').strip().split(' ')
            parameters=str(m.group(3)).strip().split(' ')
            # TODO: Do we need a more platform-independent
            # way of spliting lines?
            description=' '.join([line.strip() for line in str(m.group(3)).split('\n')]) # remove newlines and indents # noqa: E501 # pylint: disable = line-too-long
            self.commandLineOptions.append(CommandLineOption(
                options,description=description,paramsAfter=parameters))

    def __unHtml(self,html:str,preformatted:bool=False)->str:
        """
        Attempts to convert a chunk of html into plain text.
        """
        if not preformatted:
            html=html.replace('\n',' ')
        html=html.split('<')
        def decodeTag(tag:str,contents:str='')->str:
            """
            Decode a single tag
            """
            tag=tag.split('/',1)[0].split(' ',1)[0].lower()
            if tag in ['br','p','div','h1','h2','h3','h4','table','tr']:
                return '\n'+contents
            elif tag =='td':
                return '\t'+contents
            return ' '+contents
        html=html[0]+(''.join([decodeTag(*h.rsplit('>',1)) for h in html[1:]]))
        html=html.replace('  ',' ').split('&')
        ampcodes={
            'gt':'>',
            'lt':'<',
            'minus':'-',
            'plus':'+',
            'nbsp':' ',
            'amp':'&'}
        def decodeAmpresand(ampcode:str,remainder:str)->str:
            """
            decode a single html apresand code
            """
            if ampcode in ampcodes:
                remainder=ampcodes[ampcode]+remainder
            return remainder
        html=html[0]+''.join([
            decodeAmpresand(*h.split(';',1)) for h in html[1:]])
        return html.replace(' .','.').replace(' ,',',')

    def __toHtml(self,text:str)->str:
        """
        Attempts to convert a chunk of text into html.
        """
        text=text.replace('&','&amp;')
        ampcodes={'gt':'>','lt':'<','minus':'-','plus':'+'}
        for k,v in list(ampcodes.items()):
            text=text.replace(v,'&'+k+';')
        text=text.replace('  ',' &nbsp;')
        text=text.replace('\n','<br />\n')
        return text

    def __getCommandLineOptionsFromHtml(self,
        html:str
        )->typing.Iterable[CommandLineOption]:
        """
        Searches some html for command line options.

        Mostly this is for formatted man pages, but if you feed
        it any random thing, it will give it the ol' college try!
        """
        self.helpHtml=html
        if html.find('meta name="generator" content="groff'): # indicates this is an html man page # noqa: E501 # pylint: disable = line-too-long
            #sectionRe=r"""<h2>\s*([^\s<]+).*?<p[^>]*>(.*?)(?=</p>)""" # old one # noqa: E501 # pylint: disable = line-too-long
            sectionRe=r"""<h2>\s*([^\s<]+).*?<p[^>]*>(.*?)(?:(?=</p>\s*?<(?:h2|/body)>))""" # noqa: E501 # pylint: disable = line-too-long
            sectionRe=re.compile(sectionRe,re.MULTILINE|re.DOTALL)
            sections={}
            for m in sectionRe.finditer(html):
                sections[m.group(1)]=m.group(2)
            if 'DESCRIPTION' in sections:
                self.description=self.__unHtml(sections['DESCRIPTION'])
            elif 'NAME' in sections:
                self.description=self.__unHtml(sections['NAME'])
            if 'SYNOPSIS' in sections:
                plaintext=self.__unHtml(
                    sections['SYNOPSIS'].replace('</b>',' .... '),
                    preformatted=True)
                self.__getCommandLineOptionsFromText(plaintext)
            if len(self.commandLineOptions)<1 and 'DESCRIPTION' in sections: # try to get from description # noqa: E501 # pylint: disable = line-too-long
                plaintext=self.__unHtml(sections['DESCRIPTION'])
                self.__getCommandLineOptionsFromText(plaintext)
        else:
            print('WARN: Unknown HTML format.  Trying anyway...')
            plaintext=self.__unHtml(html)
            self.__getCommandLineOptionsFromText(plaintext)

    def __getCommandLineOptionsFromAppHelp(self,
        cmdline:str
        )->typing.Iterable[CommandLineOption]:
        """
        Tries to get the command line options for a program from
        the program itsself.

        TODO: If the program accidentilly starts in interactive mode, then
        we need a way to bust out after a period of time!
        """
        cmd=self.app+' '+cmdline
        po=subprocess.Popen(cmd,
            stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
        out,_=po.communicate()
        self.__getCommandLineOptionsFromText(out)

    def __getCommandLineOptionsFromMan(self
        )->typing.Iterable[CommandLineOption]:
        """
        Tries to get the command line options for a program from
        its registered man page.
        """
        cmd='man --html=cat '+self.app
        po=subprocess.Popen(cmd,
            stderr=subprocess.PIPE,stdout=subprocess.PIPE,shell=True)
        out,_=po.communicate()
        self.__getCommandLineOptionsFromHtml(out)

    def getDescription(self,
        stripNewlines:bool=False,
        lineWrap:typing.Optional[bool]=None
        )->str:
        """
        Gets the description of the program if available.

        You can choose to strip off newlines in the description for placing in
        tables, or line wrap the result to any width you want.
        """
        return self._lineWrap(self.description,stripNewlines,lineWrap)

    def _lineWrap(self,
        text:str,
        stripNewlines:bool=False,
        cols:typing.Union[None,int,bool]=None
        )->str:
        """
        Word wraps some text.

        You can choose to strip off newlines in the description for placing in
        tables, or line wrap the result to any width you want.
        """
        text=text.strip()
        if text:
            if stripNewlines:
                text=text.replace('\n','')
            if cols is not None:
                if isinstance(cols,bool):
                    if cols:
                        cols=80
                    else:
                        cols=None
                a=[]
                for line in text.split('\n'):
                    newLine=[]
                    count=0
                    words=line.split(' ')
                    for w in words:
                        nextcount=len(w)
                        if count+nextcount>cols:
                            a.append(' '.join(newLine))
                            newLine=[]
                            count=0
                        newLine.append(w)
                        count=count+nextcount+1
                    a.append(' '.join(newLine))
                text='\n'.join(a)
        return text


def main(args:typing.Iterable[str])->int:
    """
    This generates help for a command line app from the command line.

    :args: command line parameters WITOUT sys.argv[0]
    """
    printhelp=False
    cmd=None
    infoFrom=[]
    out=[]
    for arg in args:
        if cmd is None:
            if arg[0]=='-':
                if arg[1]=='-':
                    arg=arg.split('=',1)
                    if arg[0]=='--out':
                        out.append(arg[-1])
                    else:
                        print('Unrecognized parameter: '+arg[0])
                        printhelp=True
                else:
                    print('Unrecognized parameter: '+arg)
                    printhelp=True
            else:
                cmd=arg
        else:
            infoFrom.append(arg)
    if cmd is None:
        print('ERR: no cmd specified.')
        printhelp=True
    if printhelp:
        print('USAGE:')
        print('\thelpfiles.py --out=filename [--out=filename ...] cmd [get_info_from]') # noqa: E501 # pylint: disable = line-too-long
        print('PARAMS:')
        print('\t--out=<filename> ..... output to save.  If filename is just an extension, save to stdout.') # noqa: E501 # pylint: disable = line-too-long
        print('\t\tcurrently supports: ".txt" (default), ".html", or ".chm"')
        print('EXAMPLES:')
        print('\tAutomatically generate help for "ls" to the file "ls.html":')
        print('\t\thelpfiles.py --out=ls.html ls')
        print('\tAutomatically generate help for "ls" to stdout:')
        print('\t\thelpfiles.py --out=.html ls')
        print('\tAutomatically generate help as plain text:')
        print('\t\thelpfiles.py --out=.txt ls')
        print('\tGenerate the help by calling the command with --help:')
        print('\t\thelpfiles.py --out=.html ls ls --help')
        print('\t... or just let helpfiles make the assumption:')
        print('\t\thelpfiles.py --out=.html ls --help')
        print('\tGenerate the help from the command\'s manpage:')
        print('\t\thelpfiles.py --out=.html ls man')
        print('\tGenerate the help from a webpage to plain text:')
        print('\t\thelpfiles.py --out=.txt ls http://www.foo.com/ls.html')
        print('\t... or a local file:')
        print('\t\thelpfiles.py --out=.txt ls ls.html')
        print('\t... same idea only opposite direction:')
        print('\t\thelpfiles.py --out=.html ls README.txt')
    else:
        from pathlib import Path
        wrapper=HelpSystemEntry(cmd)
        wrapper.getCommandLineOptions(' '.join(infoFrom))
        if len(out)==0:
            out.append('.txt')
        for o in out:
            path=Path(o)
            if path.suffix in ('.html','.htm'):
                data=wrapper.getHelpHtml()
            elif path.suffix=='chm':
                data=wrapper.getHelpChm()
            else: # the default is .txt
                data=wrapper.getHelpText()
            if path.stem in ('','-'):
                print(data)
            else:
                path.write_text(data,'utf-8',errors='ignore')


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))
