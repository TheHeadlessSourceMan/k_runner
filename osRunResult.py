"""
result of an OsRun operation
"""
import typing
import json


class OsRunResult:
    """
    result of an OsRun operation
    """

    def __init__(self,returncode:int,stdout:str,stderr:str,stdouterr:str):
        self.returncode:int=returncode
        self.stdout:str=stdout
        self.stderr:str=stderr
        self.stdouterr:str=stdouterr # stdout and stderr intermixed as you'd see it on the terminal # noqa: E501 # pylint: disable=line-too-long
        self.finished:bool=True

    def __eq__(self,v:typing.Any)->bool:
        if isinstance(v,(int,float)):
            return self.returncode==int(v)
        return False
    def __ne__(self,v:typing.Any)->bool:
        return not (self==v)

    @property
    def value(self)->int:
        """
        Get the return value (int) from the program
        """
        return self.returncode
    __int__=value
    __float__=value

    @property
    def json(self)->str:
        """
        Get these results as a json string
        """
        return json.dumps(self.jsonObj)
    @json.setter
    def json(self,jsonString:typing.Union[str,bytes]):
        if isinstance(jsonString,bytes):
            jsonString=jsonString.decode('utf-8','ignore')
        self.jsonObj=json.loads(jsonString)

    def __iter__(self):
        return iter(self.stdouterr.split('\n'))

    def __len__(self):
        return len(self.stdouterr)

    def __len_alt__(self):
        """
        overwriting this so that if statements work
        """
        if self.succeeded:
            return 1
        return 0

    @property
    def jsonObj(self)->typing.Dict[str,typing.Any]:
        """
        Return these results as a JSON-compatible object
        """
        ret:typing.Dict[str,typing.Any]={}
        ret['returncode']=self.returncode
        if not self.finished:
            ret['finished']=self.finished
        if self.stdout is not None and self.stdout:
            ret['stdout']=self.stdout
        if self.stderr is not None and self.stderr:
            ret['stderr']=self.stderr
        if self.stdouterr is not None and self.stdouterr:
            ret['stdouterr']=self.stdouterr
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.returncode=jsonObj.get('returncode','')
        self.finished=jsonObj.get('finished',True)
        self.stdout=jsonObj.get('stdout','')
        self.stderr=jsonObj.get('stderr','')
        self.stdouterr=jsonObj.get('stdouterr','')

    def load(self,filename:str)->None:
        """
        load these run results from a file
        """
        f=open(filename,'rb')
        self.json=f.read().decode('utf-8','ignore')
        f.close()

    def save(self,filename:str)->None:
        """
        save these run results to a file
        """
        f=open(filename,'wb')
        f.write(self.json.encode('utf-8'))
        f.close()

    def __cmp__(self,other):
        """
        can do
            ==bool # for whether or not the result was successful
            ==int # to compare against returncode
            ==str # to compare a string against the combined string buffer
            ==OsRunResult # to see if this matches exactly another result
        """
        if isinstance(other,bool):
            return self.succeeded==other
        if isinstance(other,int):
            return self.returncode==other
        if isinstance(other,str):
            return self.stdouterr==other
        if isinstance(other,OsRunResult):
            return (self.returncode==other.returncode and
                self.finished==other.finished and
                self.stdouterr==other.stdouterr and
                self.stdout==other.stdout and
                self.stderr==other.stderr)
        raise TypeError()

    @property
    def out(self):
        """
        same as stdout
        """
        return self.stdout
    stdOut=out
    stdOutLines=out
    stdoutlines=out
    stdoutLines=out

    @property
    def err(self):
        """
        same as stderr
        """
        return self.stderr
    stdErr=err
    stdErrLines=err
    stderrlines=err

    @property
    def stdOutErr(self):
        """
        Combined stdout and stderr
        """
        return self.stdouterr
    stdOuterr=stdOutErr
    stdOutErrLines=stdOutErr
    stdOuterrlines=stdOutErr
    outErr=stdOutErr
    outerr=stdOutErr
    outerrLines=stdOutErr
    outErrLines=stdOutErr

    @property
    def succeeded(self):
        """
        judging by the returncode and stderr,
        determine if the command succeeded

        NOTE: assumption not always the case.
        be sure to check your command's documentation before using.
        """
        return self.returncode==0 and not self.stderr

    @property
    def failed(self):
        """
        judging by the returncode and stderr,
        determine if the command succeeded

        NOTE: assumption not always the case.
        Be sure to check your command's documentation before using.
        """
        return not self.succeeded

    def __repr__(self):
        return self.stdouterr
OsRunResults=OsRunResult
