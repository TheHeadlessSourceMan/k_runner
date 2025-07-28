"""
Exceptions when dealing with processes
"""

class ProcessException(Exception):
    """
    Something bad happened with a process
    """

class ProcessNotSpecifedException(ProcessException):
    """
    You are attempting something that requires a process
    but you have not specified one.
    """
    def __init__(self,whatIsHappening:str="do something"):
        msg=f'You are attempting to {whatIsHappening} which requires a process but you have not specified one.' # noqa: E501 # pylint: disable=line-too-long
        ProcessException.__init__(self,msg)
