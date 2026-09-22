"""
Press keyboard keys
"""
import typing
import time
import ctypes
import win32gui
import win32api
import win32con


# Map virtual key codes for media keys
# normally found in winuser.h
# see also:
#  https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes
VK_CANCEL=0x03
VK_BACK=0x08
VK_TAB=0x09
VK_RETURN=0x0D
VK_SHIFT=0x10
VK_CONTROL=0x11
VK_MENU=0x12
VK_CAPITAL=0x14
VK_ESCAPE=0x1B
VK_SPACE=0x20
VK_PRIOR=0x21
VK_NEXT=0x22
VK_END=0x23
VK_HOME=0x24
VK_LEFT=0x25
VK_UP=0x26
VK_RIGHT=0x27
VK_DOWN=0x28
VK_DELETE=0x2E
VK_LWIN=0x5B
VK_RWIN=0x5C
VK_APPS=0x5D
VK_SLEEP=0x5F
VK_F1=0x70
VK_F2=0x71
VK_F3=0x72
VK_F4=0x73
VK_F5=0x74
VK_F6=0x75
VK_F7=0x76
VK_F8=0x77
VK_F9=0x78
VK_F10=0x79
VK_F11=0x7A
VK_F12=0x7B
VK_F13=0x7C
VK_F14=0x7D
VK_F15=0x7E
VK_F16=0x7F
VK_F17=0x80
VK_F18=0x81
VK_F19=0x82
VK_F20=0x83
VK_F21=0x84
VK_F22=0x85
VK_F23=0x86
VK_F24=0x87
VK_LSHIFT=0xA0
VK_RSHIFT=0xA1
VK_LCONTROL=0xA2
VK_RCONTROL=0xA3
VK_LMENU=0xA4
VK_RMENU=0xA5
VK_BROWSER_BACK=0xA6
VK_BROWSER_FORWARD=0xA7
VK_BROWSER_REFRESH=0xA8
VK_BROWSER_STOP=0xA9
VK_BROWSER_SEARCH=0xAA
VK_BROWSER_FAVORITES=0xAB
VK_BROWSER_HOME=0xAC
VK_VOLUME_MUTE=0xAD
VK_VOLUME_DOWN=0xAE
VK_VOLUME_UP=0xAF
VK_MEDIA_NEXT_TRACK=0xB0
VK_MEDIA_PREV_TRACK=0xB1
VK_MEDIA_STOP=0xB2
VK_MEDIA_PLAY_PAUSE=0xB3
WindowsVkKeyCodes:typing.Dict[str,int]={
    "PLAY":VK_MEDIA_PLAY_PAUSE,
    "PAUSE":VK_MEDIA_PLAY_PAUSE,
    "PLAYPAUSE":VK_MEDIA_PLAY_PAUSE,
    "STOP":VK_MEDIA_STOP,
    "VOLUP":VK_VOLUME_UP,
    "VOLUMEUP":VK_VOLUME_UP,
    "VOLDOWN":VK_VOLUME_DOWN,
    "VOLUME_DOWN":VK_VOLUME_DOWN,
    "MUTE":VK_VOLUME_MUTE,
    "VOLMUTE":VK_VOLUME_MUTE,
    "VOLUME_MUTE":VK_VOLUME_MUTE,
    "SKIP":VK_MEDIA_NEXT_TRACK,
    "NEXT":VK_MEDIA_NEXT_TRACK,
    "PREVIOUS":VK_MEDIA_PREV_TRACK,
    "PREV":VK_MEDIA_PREV_TRACK,
    "SKIPTRACK":VK_MEDIA_NEXT_TRACK,
    "NEXTTRACK":VK_MEDIA_NEXT_TRACK,
    "PREVIOUSTRACK":VK_MEDIA_PREV_TRACK,
    "PREVTRACK":VK_MEDIA_PREV_TRACK,
    "CTRLBREAK":VK_CANCEL,
    "CANCEL":VK_CANCEL,
    "BACK":VK_BACK,
    "BACKSPACE":VK_BACK,
    "TAB":VK_TAB,
    "RETURN":VK_RETURN,
    "ENTER":VK_RETURN,
    "SHIFT":VK_SHIFT,
    "CONTROL":VK_CONTROL,
    "CTRL":VK_CONTROL,
    "COMMAND":VK_CONTROL,
    "MENU":VK_MENU,
    "ALT":VK_MENU,
    "OPTION":VK_CONTROL,
    "OPTIONS":VK_CONTROL,
    "CAPITAL":VK_CAPITAL,
    "CAPSLOCK":VK_CAPITAL,
    "CAPS":VK_CAPITAL,
    "ESCAPE":VK_ESCAPE,
    "ESC":VK_ESCAPE,
    "PRIOR":VK_PRIOR,
    "PAGEUP":VK_PRIOR,
    "PAGEDOWN":VK_NEXT,
    "VK_NEXT":VK_NEXT,
    "END":VK_END,
    "HOME":VK_HOME,
    "LEFT":VK_LEFT,
    "LEFTARROW":VK_LEFT,
    "UP":VK_UP,
    "UPARROW":VK_UP,
    "RIGHTARROW":VK_RIGHT,
    "RIGHT":VK_RIGHT,
    "DOWNARROW":VK_DOWN,
    "DOWN":VK_DOWN,
    "DELETE":VK_DELETE,
    "DEL":VK_DELETE,
    "LWIN":VK_LWIN,
    "WINDOWS":VK_LWIN,
    "APPLE":VK_LWIN,
    "RWIN":VK_RWIN,
    "APPS":VK_APPS,
    "SLEEP":VK_SLEEP,
    "F1":VK_F1,
    "F2":VK_F2,
    "F3":VK_F3,
    "F4":VK_F4,
    "F5":VK_F5,
    "F6":VK_F6,
    "F7":VK_F7,
    "F8":VK_F8,
    "F9":VK_F9,
    "F10":VK_F10,
    "F11":VK_F11,
    "F12":VK_F12,
    "F13":VK_F13,
    "F14":VK_F14,
    "F15":VK_F15,
    "F16":VK_F16,
    "F17":VK_F17,
    "F18":VK_F18,
    "F19":VK_F19,
    "F20":VK_F20,
    "F21":VK_F21,
    "F22":VK_F22,
    "F23":VK_F23,
    "F24":VK_F24,
    "LSHIFT":VK_LSHIFT,
    "LEFTSHIFT":VK_LSHIFT,
    "RSHIFT":VK_RSHIFT,
    "RIGHTSHIFT":VK_RSHIFT,
    "LCONTROL":VK_LCONTROL,
    "LEFTCONTROL":VK_LCONTROL,
    "RIGHTCONTROL":VK_RCONTROL,
    "RCONTROL":VK_RCONTROL,
    "LMENU":VK_LMENU,
    "LEFTMENU":VK_LMENU,
    "RMENU":VK_RMENU,
    "RIGHTMENU":VK_RMENU,
    "BROWSER_BACK":VK_BROWSER_BACK,
    "BROWSER_FORWARD":VK_BROWSER_FORWARD,
    "BROWSER_REFRESH":VK_BROWSER_REFRESH,
    "BROWSER_STOP":VK_BROWSER_STOP,
    "BROWSER_SEARCH":VK_BROWSER_SEARCH,
    "BROWSER_FAVORITES":VK_BROWSER_FAVORITES,
    "BROWSER_HOME":VK_BROWSER_HOME,
}


# C struct definitions for SendInput API
PUL=ctypes.POINTER(ctypes.c_ulong)


class KEYBDINPUT(ctypes.Structure):
    """
    Windows KEYBDINPUT struct
    """
    _fields_=[
        ("wVk",ctypes.c_ushort),
        ("wScan",ctypes.c_ushort),
        ("dwFlags",ctypes.c_ulong),
        ("time",ctypes.c_ulong),
        ("dwExtraInfo",PUL)]


class INPUT(ctypes.Structure):
    """
    Windows INPUT struct
    """
    class _INPUT(ctypes.Union):
        _fields_=[("ki",KEYBDINPUT)]
    _anonymous_=("_input",)
    _fields_=[("type",ctypes.c_ulong),("_input",_INPUT)]


def asKeyCode(keyCode:typing.Union[int,str])->int:
    """
    Convert a single shorthand to os key code
    """
    if isinstance(keyCode,int):
        return keyCode
    if len(keyCode)==1:
        # regular key
        encoded=ord(keyCode)
        return ctypes.windll.User32.VkKeyScanW(encoded)
    # special key
    keyCode=keyCode.replace('[','').replace(']','').strip()\
        .replace(' ','').replace('VK_','').replace('_','')
    modifierList=keyCode.split('+')
    ret=0
    for kc in modifierList:
        if len(kc)==0:
            ret|=asKeyCode('+')
        elif len(kc)<2:
            ret|=asKeyCode(kc)
        else:
            kc=keyCode.upper()
            kcVal=WindowsVkKeyCodes.get(kc)
            if kcVal is None:
                raise EncodingWarning(
                    f'Unable to translate "{kc}" to keystrokes')
            ret|=kcVal
    return ret


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
    original=keyCode
    if isinstance(keyCode, str) and len(keyCode) == 1:
        vkCombo = ctypes.windll.user32.VkKeyScanW(ord(keyCode))
        keyCode = vkCombo & 0xFF
        modifiers = (vkCombo >> 8) & 0xFF
    else:
        keyCode = asKeyCode(keyCode)
        modifiers = 0
    if keyCode<=0:
        raise EncodingWarning(
            f'Unable to translate "{original}" to keystrokes')
    if not inBackground:
        if hWnd is not None:
            # Restore and bring to foreground
            windowInfo = win32gui.GetWindowPlacement(hWnd)
            if windowInfo[1] == win32con.SW_SHOWMINIMIZED:
                win32gui.ShowWindow(hWnd, win32con.SW_RESTORE)
            try:
                win32gui.SetForegroundWindow(hWnd)
            except Exception:
                pass
        # Use SendInput for foreground typing
        extra = ctypes.c_ulong(0)
        ii = INPUT._INPUT()
        ii.ki = KEYBDINPUT(keyCode, 0, 0, 0, ctypes.pointer(extra))
        input_struct = INPUT(ctypes.c_ulong(1), ii)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))
        time.sleep(0.01)
        ii.ki = KEYBDINPUT(keyCode, 0, 2, 0, ctypes.pointer(extra))
        input_struct = INPUT(ctypes.c_ulong(1), ii)
        ctypes.windll.user32.SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))
    else:
        if hWnd is None:
            return  # Cannot send to background with no hWnd

        scanCode = win32api.MapVirtualKey(keyCode, 0)
        lParam_down = 0x00000001 | (scanCode << 16)
        lParam_up = 0xC0000001 | (scanCode << 16)

        # Send modifiers first if necessary
        if modifiers & 1:  # Shift
            modScan = win32api.MapVirtualKey(VK_SHIFT, 0)
            win32gui.SendMessage(hWnd, win32con.WM_KEYDOWN, VK_SHIFT, 0x00000001 | (modScan << 16))
        if modifiers & 2:  # Ctrl
            modScan = win32api.MapVirtualKey(VK_CONTROL, 0)
            win32gui.SendMessage(hWnd, win32con.WM_KEYDOWN, VK_CONTROL, 0x00000001 | (modScan << 16))
        if modifiers & 4:  # Alt
            modScan = win32api.MapVirtualKey(VK_MENU, 0)
            win32gui.SendMessage(hWnd, win32con.WM_KEYDOWN, VK_MENU, 0x00000001 | (modScan << 16))

        win32gui.SendMessage(hWnd, win32con.WM_KEYDOWN, keyCode, lParam_down)
        if 0x30 <= keyCode <= 0x5A:  # A-Z, 0-9
            win32gui.SendMessage(hWnd, win32con.WM_CHAR, keyCode, lParam_down)
        time.sleep(0.01)
        win32gui.SendMessage(hWnd, win32con.WM_KEYUP, keyCode, lParam_up)

        # Release modifiers
        if modifiers & 4:
            win32gui.SendMessage(hWnd, win32con.WM_KEYUP, VK_MENU, 0xC0000001 | (modScan << 16))
        if modifiers & 2:
            win32gui.SendMessage(hWnd, win32con.WM_KEYUP, VK_CONTROL, 0xC0000001 | (modScan << 16))
        if modifiers & 1:
            win32gui.SendMessage(hWnd, win32con.WM_KEYUP, VK_SHIFT, 0xC0000001 | (modScan << 16))
sendKeyboard=sendKeyboardKey
pressKey=sendKeyboardKey
sendKey=sendKeyboardKey


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
    # ALTERNATIVE:
    # import win32com.client
    # shell = win32com.client.Dispatch("WScript.Shell")
    # for c in keys:
    #     if c=='\r':
    #         continue
    #     if c=='\n':
    #         c='~'
    #     if shift:
    #         c='+'+c
    #     if ctrl:
    #         c='^'+c
    #     if alt:
    #         c=r'%'+c
    #     shell.SendKeys(c,0)
    nextCharEscaped=False
    buildingSpecial:typing.List[str]=[]
    for c in keyStream:
        if buildingSpecial:
            buildingSpecial.append(c)
            if c==']':
                sendKeyboardKey(''.join(buildingSpecial),hWnd,inBackground)
                if timeDelaySec>0:
                    time.sleep(timeDelaySec)
                buildingSpecial=[]
        else:
            if nextCharEscaped:
                sendKeyboardKey(c,hWnd,inBackground)
                if timeDelaySec>0:
                    time.sleep(timeDelaySec)
                nextCharEscaped=False
            elif c=='\\':
                nextCharEscaped=True
            elif c=='[':
                buildingSpecial.append(c)
            else:
                sendKeyboardKey(c,hWnd,inBackground)
                if timeDelaySec>0:
                    time.sleep(timeDelaySec)
sendKeyboard=sendKeyboardKeys
pressKeys=sendKeyboardKeys
sendKeys=sendKeyboardKeys


def main(args:typing.Iterable[str])->int:
    """
    Run like from the command line.

    Does not expect args[0] to be program name.
    """
    printHelp=False
    if not args:
        printHelp=True
    else:
        for arg in args:
            if arg in ('-h','--help'):
                printHelp=True
            sendKeyboardKeys(arg)
    if printHelp:
        print('USAGE:')
        print('   keyboardKeys [keys]')
        print('EXAMPLE:')
        print('   pressKeys [CTRL+C] hello [PLAY] [VOLUME_UP]')
        return -1
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
