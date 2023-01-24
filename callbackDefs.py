"""
types for common callbacks for logging file output
"""
import typing

LineCallback=typing.Callable[[str],None] # called once per each line
CharacterCallback=typing.Callable[[str],None] # called once per each character

class ApplicationCallbacks:
    stdoutLine:LineCallback
    stdoutCharacter:CharacterCallback
    stderrLine:LineCallback
    stderrCharacter:CharacterCallback
    line:LineCallback
    character:CharacterCallback