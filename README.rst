cmdhelper
=========

cmdhelper is a Python utility for writing command line scripts with a
consistent style, default set of command line options, and common
approach to logging.

cmdhelper provides:

-  Parsing of command line options using either argparse or optparse.

-  Setup of logging with the possibility to copy stdout or stderr into
   the logfile.

-  Definition of a set of default options, including options to set
   verbosity and logging options.

-  A utility function to run external commands whose output can be
   logged and parsed for error messages.

-  A utility function for asking the user to confirm actions.

Example
-------

A script that processes different commands with optional command
arguments might include:

::

    from cmdhelper import *

    cmdHelper = CmdHelper('argparse', __version__)
    cmdHelper.add_argument('cmd', help='command')
    cmdHelper.add_argument('args', help='command arguments', nargs='*')
    options = cmdHelper.parse()

    try:
        # processing goes here

    except Exception as e:
         handleError(e)

Running the above code with –help will produce the following output:

::

    usage: example.py [-h] [--version] [-i] [-v] [--debug] [--noscreen]
                      [--logfile LOGFILE] [--loglevel LOGLEVEL]
                      [--logseparator LOGSEPARATOR]
                      [--logtimestampfmt LOGTIMESTAMPFMT]
                      cmd [args [args ...]]

    positional arguments:
      cmd                   command
      args                  command arguments

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit
      -i, --interactive     enter interactive Python at completion
      -v, --verbose         verbose output
      --debug               debugging output
      --noscreen            disable logging output to screen
      --logfile LOGFILE     write logging information to this file (default: )
      --loglevel LOGLEVEL   logging level for logfile (default: INFO, unless
                            --debug is given)
      --logseparator LOGSEPARATOR
                            message to write to logfile at beginning of new log
      --logtimestampfmt LOGTIMESTAMPFMT
                            timestamp format string (in logging formatter format)

