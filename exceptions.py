"""
Exceptions that this package can cause
"""
import typing


class OsRunException(Exception):
    """
    Thrown when there is a problem running a given command
    """
    def __init__(self,
        cmd:typing.List[str],
        cause:typing.Optional[Exception]=None):
        """ """
        self.cmd=cmd
        self.cause=cause
        msg=f'Trouble running:\n\t{cmd}'
        if cause is not None:
            aMsg=[f'{msg}\nCaused by:']
            aMsg.extend(str(cause).split('\n'))
            msg='\n\t'.join(aMsg)
        Exception.__init__(self,msg)
