"""
Tools for managing environment variables
"""
import typing
from pathlib import Path


EnvironmentVariablesCompatible=typing.Union[
    str,typing.Dict[str,typing.Any],"EnvironmentVariables",
    typing.Iterable["EnvironmentVariablesCompatible"]]


def asEnvironmentVariables(
    env:EnvironmentVariablesCompatible
    )->"EnvironmentVariables":
    """
    Always return as EnvironmentVariables object.

    If it already is one, retun as-is
    """
    if isinstance(env,EnvironmentVariables):
        return env
    return EnvironmentVariables(env)


class EnvironmentVariables:
    """
    Manage a set of environment variables
    """

    def __init__(self,env:typing.Optional[EnvironmentVariablesCompatible]=None):
        """
        Manage environment variables
        """
        self._env:typing.Dict[str,str]={}
        self.append(env)

    def __getitem__(self,idx:str)->str:
        """
        Access like a dict
        """
        return self._env[idx]

    def __setitem__(self,idx:str,value:typing.Any)->None:
        """
        Access like a dict
        """
        self._env[idx]=str(value)

    def __delitem__(self,idx:str)->None:
        """
        Access like a dict
        """
        del self._env[idx]

    def __len__(self)->int:
        """
        Access like a dict
        """
        return len(self._env)

    def items(self)->typing.Iterator[typing.Tuple[str,str]]:
        """
        Access like a dict
        """
        return self._env.items() # type: ignore

    @property
    def envString(self)->str:
        """
        This data as a json-compatible string
        """
        ret:typing.List[str]=[]
        for k,v in self._env.items():
            ret.append(f'{k}={v}')
        return '\n'.join(ret)
    @envString.setter
    def envString(self,envString:str):
        self.assign(envString)

    def __str__(self)->str:
        return self.envString

    @property
    def jsonString(self)->str:
        """
        This data as a json-compatible string
        """
        import json
        return json.dumps(self._env)
    @jsonString.setter
    def jsonString(self,jsonString:str):
        import json
        self.jsonObj=json.loads(jsonString)
    @property
    def jsonObj(self)->typing.Dict[str,str]:
        """
        This data as a json-compatible object
        """
        return dict(self._env)
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.assign(jsonObj)

    def load(self,
        filename:typing.Union[str,Path],
        appendToExisting:bool=False):
        """
        Load from file (either a .env or a .json)
        """
        if not appendToExisting:
            self.clear()
        if not isinstance(filename,Path):
            filename=Path(filename)
        data=filename.read_text('utf-8',errors='ignore')
        self.append(data)

    def save(self,
        filename:typing.Union[str,Path]):
        """
        Save to file (either a .env or a .json)
        """
        if not isinstance(filename,Path):
            filename=Path(filename)
        if filename.suffix=='.env':
            data=self.jsonString
        else:
            data=self.envString
        filename.write_text(data,'utf-8',errors='ignore')

    def union(self,env:EnvironmentVariablesCompatible):
        """
        Create a new environment variables list
        that is a union of lists.
        """
        newEnv=EnvironmentVariables(self)
        newEnv.append(env)
        return newEnv

    def clear(self)->None:
        """
        Clear environment variables
        """
        self._env.clear()

    def assign(self,
        env:typing.Optional[EnvironmentVariablesCompatible]=None
        )->None:
        """
        Assign all environment variables
        """
        self.clear()
        self.append(env)

    def append(self,
        env:typing.Optional[EnvironmentVariablesCompatible]=None
        )->None:
        """
        Append more environment variables
        """
        if env is None:
            return
        if isinstance(env,str):
            # determine whether it is json or .env
            env=env.lstrip()
            if env and env[0] in ('{','['):
                import json
                for k,v in json.loads(env):
                    self._env[k]=str(v)
            else:
                for line in env.split('\n'):
                    line=line.strip()
                    if line.startswith('#'):
                        continue
                    kv=line.split('=',1)
                    if len(kv)!=2:
                        continue
                    self._env[kv[0].rstrip()]=kv[1].lstrip()
        elif isinstance(env,(dict,EnvironmentVariables)):
            for k,v in env.items():
                self._env[str(k)]=str(v)
        else:
            for e in env:
                self.append(e)
    extend=append
    update=append


def getCurrentEnvironmentVariables()->EnvironmentVariables:
    """
    Return the current environment variables of this process
    """
    import os
    return EnvironmentVariables(os.environ)
