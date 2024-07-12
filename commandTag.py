"""
Given an xml tag of the form
    <command id="my_cmd" cmd="something" />
Or a tag with a bunch of those in it
Will execute the command and return the results.
"""
import typing
from collections.abc import Iterable,Mapping
from lxml import etree
from k_runner import osrun
from paths import URLCompatible,asURL,URL


class CommandFailedException(Exception):
    """
    Exception for when executing a command fails
    """
    def __init__(self,cmd:str,onWhat:str,info:typing.Any):
        self.cmd=cmd
        self.info=info
        msg=[
            'Command:',
            '--------',
            f'   {cmd}',
            'Failed on:',
            '----------',
            f'   {onWhat}'
            'Info:',
            '-----',
            f'   {info}']
        Exception.__init__(self,'\n'.join(msg))
class CommandFailedOnReturncodeException(CommandFailedException):
    """
    Exception for when the return value of a shell command is nonzero
    """
    def __init__(self,cmd:str,info:int):
        CommandFailedException.__init__(self,cmd,'Return Code',info)
class CommandFailedOnStderrException(CommandFailedException):
    """
    Exception for when messages come out on the stderr stream
    of a shell command
    """
    def __init__(self,cmd:str,info:str):
        CommandFailedException.__init__(self,cmd,'Stderr',info)
class CommandFailedOnMissingArgumentException(CommandFailedException):
    """
    Exception for when two few arguments are supplied
    """
    def __init__(self,cmd:str,info:int):
        CommandFailedException.__init__(self,cmd,'Missing Argument',info)

def commandTag(
    cmdTag:typing.Union[URLCompatible,str,etree.Element],
    **kwargs
    )->typing.Dict[str,osrun.OsRunResult]:
    """
    Given an xml tag of the form
        <command id="my_cmd" cmd="something" />
    Or a tag with a bunch of those in it
    Will execute the command and return the results.

    Additional arguments will be passed to the command, eg:
        commandTag('<command cmd="do_{foo}.sh" />',foo="splat")
    Will run the command "do_splat.sh"

    Additional arguments can be anything tree-like
        (object heirarchy, dict tree, etc), eg:
        commandTag('<command cmd="do_{jsondata.x}.sh" />',foo=json.loads('{"x","splat"}'))
    Will run the command "do_splat.sh"

    You can have things in the additional arguments that are not used in any
    commands, but you cannot have any commands that rely up arguments you
    don't have. (will raise an exception)

    The additional arguments will be expanded with the results of each call:
        commandTag('<div><command id="x_cmd" cmd="x.sh" /><command cmd="y.sh {x_cmd.stdout}" /></div>')

    Allows nested commands for structure
        commandTag('<command id="a"><command id="b" /><command id="c" /></command>')
    Which is functionally the same as:
        commandTag('<command id="b" /><command id="c" /><command id="a" />')
    Only possibly clearer to the reader what the intended purpose is.

    The attributes: breakOnReturncode,breakOnStderr (both True by default)
        can be used to control when to bail out.

    :cmdTag: can be an lxml element, an xml string, 
        or a Url of an object to download

    On simple example of using this is
    (note: doesn't handle fancy things like terminal controls, etc):
        <head>
        <script>
            const commandApi="http://127.0.0.1:8101/command?cmdTag=";
            async function doCommand(elWithCommands){
                const url=commandApi+encodeURIComponent(elWithCommands.outerHTML);
                const response=await fetch(
                    url,
                    {
                        method:"GET",
                        headers:{'Accept':'application/json'}
                    }
                );
                var target=elWithCommands.nextElementSibling;
                while(target!=null){
                    if(target.classList.contains('results')){
                        var txt="";
                        const json=await response.json();
                        for(const [key,value] of Object.entries(json)) {
                            txt+=`<div class="result_block"><div class="result_block_title">${key}</div><pre>${value.stdouterr}</pre></div>`
                        }
                        target.innerHTML=txt;
                        break;
                    }
                    target=target.nextElementSibling;
                }
            }
        </script>
        <style>
            .results {background-color:black;padding:6px;}
            .results pre {font-family:terminal,'Courier New',Courier,monospace; color:lime;padding:0px 6px}
            .result_block {background-color:rgba(255,255,255,0.2);margin:6px;}
            .result_block_title {background-color:rgba(255,255,255,0.2);padding:6px;box-shadow:0px 10px 10px red}
            .button {background-color:cornflowerblue; cursor:pointer; padding:2px 6px; display:inline-block}
        </style>
    </head>
    <body>
        <div class="button" onClick="doCommand(this)">Button 1<command id="0" cmd="echo hello world" /></div>
        <div class="button" onClick="doCommand(this)">Button 2<command id="0" cmd="echo Directory listing" /><command id="1" cmd="dir c:\" /></div>
        <div class="results"></div>
    </body>
    </html>

    Returns {id:OsRunResult}
    """
    if not etree.iselement(cmdTag):
        if not isinstance(cmdTag,str):
            # NOTE: a string is always an xml string, not a URL (for security)
            url:URL=typing.cast(URL,asURL(cmdTag))
            cmdTag=url.read()
        cmdTag=etree.fromstring(cmdTag)
    results:typing.Dict[str,osrun.OsRunResult]={}
    replacements=dict(**kwargs)
    def getReplacement(s:str)->str:
        """
        get a replacenemt for the named value in the results
        this is more complicated than a mere dict lookup because
        replacements can be like "item.value.value"

        If the replacement is not found, raises
        AttributeError with the point where it broke
        """
        ret:typing.Any=replacements
        steps=s.split('.')
        for i,step in enumerate(steps):
            if isinstance(ret,Iterable): # iterable, including strings!
                try:
                    ret=ret[int(step)]
                except Exception:
                    raise AttributeError('.'.join(steps[0:i]))
            elif hasattr(ret,Mapping):
                try:
                    ret=ret[step]
                except Exception:
                    raise AttributeError('.'.join(steps[0:i]))
            else:
                try:
                    ret=getattr(ret,step)
                except Exception:
                    raise AttributeError('.'.join(steps[0:i]))
        return str(ret)
    def stringReplacement(s:str)->str:
        """
        replace "{}" in a string with replacements
        """
        ret=[]
        for i,replacement in enumerate(s.split('{')):
            if i==0:
                ret.append(replacement)
            else:
                rr=replacement.split('}',1)
                ret.append(getReplacement(rr[0]))
                if len(rr)>1 and rr[1]:
                    ret.append(rr[1])
        return ''.join(ret)
    def processTag(el:etree.Element)->None:
        """
        Process/run a single <command> tag.
        (also runs all child tags)

        Results will be stored in the results dict by their <command id=""> id
        """
        for child in el:
            processTag(child)
        if el.tag=='command':
            cmd:str=stringReplacement(el.attrib['cmd'])
            id:str=el.attrib.get('id','')
            result=osrun.run(cmd,shell=True)
            if result.stderr \
                and el.attrib.get('breakOnStderr','t')[0] in ('t','y','1'):
                raise CommandFailedOnStderrException(cmd,result.stderr)
            if result.returncode!=0 \
                and el.attrib.get('breakOnReturncode','t')[0] in ('t','y','1'):
                raise CommandFailedOnReturncodeException(
                    cmd,result.returncode)
            if id:
                replacements[id]=result
                results[id]=result
    processTag(cmdTag)
    return results

def runCommandServer(port:int=8101,**kwargs):
    """
    Starts up a command server on the given port

    WARNING: this endpoint can be a HUGE security risk
    if outside parties gain access to it!

    kwargs passed in will serve as the default args to all commands
    """
    from http.server import HTTPServer,BaseHTTPRequestHandler
    class CommandHandler(BaseHTTPRequestHandler):
        """
        For a list of http messages, see:
            http://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
        """
        def do_HEAD(self):
            """
            called on HTTP HEAD
            """
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.send_header('Access-Control-Allow-Origin','*')
            self.end_headers()

        def do_PUT(self):
            """
            called on HTTP PUT
            """
            self.send_error(404,'File not found')

        def do_GET(self):
            """
            called on HTTP GET
            """
            import json
            pq=self.path.split('?',1)
            if len(pq)<2:
                self.send_error(404,pq[0])
                return
            try:
                params:typing.Dict[str,str]=dict(kwargs)
                for p in pq[-1].split('&'):
                    kv=p.split('=',1)
                    if len(kv)<2:
                        kv.append('')
                    params[URL.urldecode(kv[0])]=URL.urldecode(kv[1])
                paramsStr=','.join([f'{k}="{v}"' for k,v in params.items()])
                print(f'command({paramsStr})')
                results={}
                for k,v in commandTag(**params).items():
                    results[k]=v.jsonObj
                jsonResults=json.dumps(results)
                print(f'Results:\n{jsonResults}')
                returnbytes=jsonResults.encode('utf-8')
                self.send_response(200)
                self.send_header('Content-type','application/json')
                self.send_header('Access-Control-Allow-Origin','*')
                self.end_headers()
                self.wfile.write(returnbytes)
            except Exception:
                import io
                import traceback
                errors=io.StringIO()
                traceback.print_exc(file=errors)
                self.send_error(500,f'ERROR:\n{errors.getvalue()}')

    server_address=('127.0.0.1',int(port))
    server=HTTPServer(server_address,CommandHandler)
    url=f'http://{server_address[0]}:{server_address[1]}/command?'
    print(f'Starting command server on {url}')
    server.serve_forever(1)


if __name__=='__main__':
    import sys
    cmds:typing.Dict[str,typing.Any]={'port':'8101'}
    for a in sys.argv[1:]:
        kv=a.split('=',1)
        if len(kv)<2:
            kv.append('')
        cmds[kv[0]]=kv[1]
    runCommandServer(**cmds)
