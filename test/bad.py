def cmdline(args):
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    print(args)
    print('Hello, everything is going fine until...')
    raise Exception('Somebody farted!')


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
