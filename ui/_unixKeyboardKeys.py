import typing


def sendKeyboardKey(
    keyCode:typing.Union[int,str],
    hWnd:typing.Optional[int]=None,
    inBackground:bool=False
    )->None:
    """
    Press one single keyboard key

    :keyCode: Supports:
        A single char text key "s"
        key names (with/without []) "PAGE_UP"
        meta keys "CTRL+C"
    :hWnd: If not specified, sends it to whatever
        is currently selected
    :inBackground: Attempt to send to a background
        window without making it foreground first. This
        is unreliable due to windows limitations, but
        could be nice in some cases.

    NOTE: if you want more complicated sequences, you may
    want to try pressKeys() instead.
    """
    raise NotImplementedError()


def sendKeyboardKeys(
    keyStream:str,
    hWnd:typing.Optional[int]=None,
    inBackground:bool=False,
    timeDelaySec:float=0.05
    )->None:
    r"""
    Press a series of keys.

    :keyStream: Supports:
        Normal letters
        special keys "[UP_ARROW]"
        meta keys "[CTRL+C]"
        and "[" key via "\["
    :hWnd: If not specified, sends it to whatever
        is currently selected
    :inBackground: Attempt to send to a background
        window without making it foreground first. This
        is unreliable due to windows limitations, but
        could be nice in some cases.
    :timeDelaySec: Time delay between keypresses
    """
    raise NotImplementedError()
