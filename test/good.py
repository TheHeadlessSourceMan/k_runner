def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    print(args)
    print('Life\'s a happy song')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
