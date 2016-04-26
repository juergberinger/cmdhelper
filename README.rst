cmdhelper
=========

cmdhelper is a Python utility for writing command line scripts with a
consistent style, default set of command line options, and common
approach to logging.

cmdhelper provides:

-  Parsing of command line options using either argparse or optparse.

-  Setup of logging with the possibility to copy stdout or stderr into
   the logfile.

-  Possibility to e-mail log messages upon completion with an option
   to send the e-mail only if a log message with a severity at or
   above a trigger level was recorded.

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
    cmdHelper.add_option('-x', '--example', dest='value', default=None, help='sample option')
    options = cmdHelper.parse()

    try:
        # processing goes here
        pass

    except Exception as e:
         handleError(e,options.debug)

Running the above code with –help will produce the following output:

::

    usage: example.py [-h] [--version] [-i] [-v] [--debug] [--noscreen]
                      [--logfile LOGFILE] [--loglevel LOGLEVEL]
                      [--logseparator LOGSEPARATOR]
                      [--logtimestampfmt LOGTIMESTAMPFMT]  [--emailto EMAILTO]
                      [--emailsubject EMAILSUBJECT] [--emaillevel EMAILLEVEL]
                      [--emailtriglevel EMAILTRIGLEVEL] [-x VALUE]
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
      --loglevel LOGLEVEL   logging level for logfile (default: INFO or DEBUG)
      --logseparator LOGSEPARATOR
                            message to write to logfile at beginning of new log
      --logtimestampfmt LOGTIMESTAMPFMT
                            timestamp format string (in logging formatter format)
      --emailto EMAILTO     email address receiving any log messages
      --emailsubject EMAILSUBJECT
                            subject for log e-mails
      --emaillevel EMAILLEVEL
                            logging level for e-mails (default: WARNING)
      --emailtriglevel EMAILTRIGLEVEL
                            trigger level for sending e-mails (default: None)
      -x VALUE, --example VALUE
                            sample option
