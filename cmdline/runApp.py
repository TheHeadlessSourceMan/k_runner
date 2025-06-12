"""
This is a tool to run programs.
"""


class RunApp():
    """
    This is a tool to run programs.
    """
    # TOOL: runApp=RunApp()

    def __init__(self):
        """
        Construct a new RunApp object
        """

    def run(self,
        cmd,
        onOutputCB=None,
        onErrorCB=None,
        hideWindows=False,
        priorityBoost=0,
        wDogOutput=None,
        wDogLifetime=None):
        """
        Run the given command line
        """
        # FN: runApp.run(cmd,onOutputCB=None,onErrorCB=None,hideWindows=False,priorityBoost=0,wDogOutput=None,wDogLifetime=None) # noqa: E501 # pylint: disable=line-too-long
        app=Application()
        app.run(cmd,onOutputCB,onErrorCB,
            hideWindows,priorityBoost,wDogOutput,wDogLifetime)

    def getVersion(self):
        """
        Returns a version string for this tool or None if not installed.
        """
        # FN: getVersion()
        return 'N/a'

    def canLoadFile(self,fileName):
        """
        Returns whether or not this tool can open the given file.
        """
        # FN: canLoadFile(fileName)
        ext=fileName.rsplit('.',1)
        if len(ext)>1 and ext[1]=='exe':
            return True
        elif len(ext)<2:
            return True
        return False
