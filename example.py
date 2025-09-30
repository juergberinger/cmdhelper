#!/usr/bin/env python

__version__ = '0.0.0'

from cmdhelper import *

cmdHelper = CmdHelper('argparse', __version__)
cmdHelper.add_argument('cmd', help='command')
cmdHelper.add_argument('args', help='command arguments', nargs='*')
cmdHelper.add_option('-x', '--example', dest='value', default=None, help='sample option')
options = cmdHelper.parse()

try:
    # processing goes here
    run('python -c "print(2)"',True)
    pass    

except Exception as e:
     handleError(e,options.debug)
