#!/usr/bin/env python
"""
This module provides tools for writing command line scripts
with a consistent style, default set of command line options, and
common approach to logging.

Typical usage:

    from cmdhelper import *
    cmdHelper = CmdHelper('argparse', __version__, 'Sample script')
    cmdHelper.add_option('-x', '--example', dest='value', default=None, help='sample option')
    ...
    args = cmdHelper.parse()
    debug('start processing')
    print 'Normal output'
    info('more details for verbose mode')
    ...
"""
__author__ = 'Juerg Beringer'
__version__ = '0.2.2'

__all__ = [ 'CmdHelper', 'CmdError', 'cmdLine', 'handleError',
            'debug', 'warning', 'info', 'error', 'critical',
            'confirm', 'run']

import sys
import os
import subprocess
import re
import time
import logging
from logging import debug, info, warning, error, critical
import smtplib
from email.mime.text import MIMEText


#
# Configure logging. Provide a NullHandler to suppress any
# logging output in case the user doesn't use logging. In
# Python 2.7 and later, NullHandler is included in logging.
# Add new level STDOUT for redirecting stdout into log file.
#
try:
    from logging.handlers import NullHandler
except ImportError:
    class NullHandler(logging.Handler):

        """Do-nothing logging handler"""

        def emit(self, record):
            pass
logging.getLogger().addHandler(NullHandler())
logging.STDOUT = 25
logging.addLevelName(logging.STDOUT, 'STDOUT')


class CmdError(Exception):

    """Error class for various command line errors."""

    def __init__(self, msg):
        Exception.__init__(self, msg)
        self.msg = msg

    def __str__(self):
        return self.msg


class LogWriter:

    """LogWriter is a writer class that can be used to redirect a stream
       such as sys.stdout to a logger. Writing to the stream will result
       in logging messages at level loglevel."""

    def __init__(self, logger, loglevel=logging.INFO):
        """Configure LogWriter to use logger at loglevel."""
        self.logger = logger
        self.loglevel = loglevel

    def write(self, text):
        """Write text. An additional attribute terminator with a value of
           None is added to the logging record to indicate that StreamHandler
           should not add a newline."""
        self.logger.log(self.loglevel, text, extra={'terminator': None})

    def flush(self):
        """Flush internal I/O buffer.

        For LogWriter, this is a dummy method provided in case it's expected."""
        pass


class MyStreamHandler(logging.StreamHandler):

    """StreamHandler with the option to omit the trailing newline by setting
       attribute terminator in the LogRecord to None. This option will be
       a standard feature in Python 3.2. Also allows to abort program
       in case of IOErrors. This is useful when logging to the console
       and there's a broken pipe e.g. due to piping into head."""

    def __init__(self, stream=None, abortOnIOError=False):
        logging.StreamHandler.__init__(self, stream)
        self.abortOnIOError = abortOnIOError

    def emit(self, record):
        """Emit a record. Unless record.terminator is set, a trailing
           newline will be written to the output stream."""
        try:
            msg = self.format(record)
            terminator = getattr(record, 'terminator', '\n')
            self.stream.write(msg)
            if terminator is not None:
                self.stream.write(terminator)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def flush(self):
        """Flush the stream.

        In contrast to StreamHandler, errors are not caught so the program doesn't iterate
        through tons of logging errors e.g. in case of a broken pipe."""
        # See /usr/lib64/python2.7/logging/__init__.py, StreamHander.flush()
        self.acquire()
        try:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        except IOError as e:
            if self.abortOnIOError:
                sys.exit('IOError: %s' % e)
            else:
                raise e
        finally:
            self.release()


class BufferingSMTPHandler(logging.handlers.BufferingHandler):

    """Logging handler that buffers messages and e-mails them once more
    than a given number of messages have been received."""

    def __init__(self, fromAddr, toAddr, subject, maxMessagesPerEmail=4096):
        logging.handlers.BufferingHandler.__init__(self, maxMessagesPerEmail)
        self.fromAddr = fromAddr
        self.toAddr = toAddr
        self.subject = subject

    def flush(self):
        if len(self.buffer) > 0:
            # Do not send empty e-mails
            text = []
            for record in self.buffer:
                terminator = getattr(record, 'terminator', '\n')
                s = self.format(record)
                if terminator is not None:
                    text.append(s + terminator)
                else:
                    text.append(s)
            msg = MIMEText(''.join(text))
            msg['From'] = self.fromAddr
            msg['To'] = self.toAddr
            msg['Subject'] = self.subject
            # print 'BufferingSMTPHandler'
            # print msg.as_string()
            smtp = smtplib.SMTP('localhost')
            smtp.sendmail(self.fromAddr, [self.toAddr], msg.as_string())
            smtp.quit()
            self.buffer = []


class ConsoleFormatter(logging.Formatter):

    """Logging formatter used for console output: prepends the log level for WARNING
       and higher levels, prepends '... ' for DEBUG and shows message otherwise."""

    def format(self, record):
        # The code below assumes that redirected stdout always comes from
        # the root logger
        if record.name != 'root':
            self._fmt = '%(levelname)-7s %(name)-30s %(message)s'
        else:
            if record.levelno > logging.STDOUT:
                self._fmt = '%(levelname)s: %(message)s'
            else:
                if record.levelno == logging.DEBUG:
                    self._fmt = '... %(message)s'
                else:
                    self._fmt = '%(message)s'
        return logging.Formatter.format(self, record)


class FileFormatter(logging.Formatter):

    """Logging formatter for log files."""

    def __init__(self, timestampFmt=None, datefmt='%a %b %d %X %Z %Y'):
        """Constructor. If timestampFmt is None, a plain format w/o timestamps
        will be used. If timestampFmt is set to a format string, this string will
        be used as timestamp for each message. Subsequent lines of multi-line
        messages will be indented by the length of the time stamp."""
        logging.Formatter.__init__(self, None, datefmt)
        self.timestampFmt = timestampFmt
        self._startLine = True

    def format(self, record):
        # NOTE: If stdout is redirected to FileFormatter, each line may arrive
        #       broken down into several messages, depending on how it was written
        #       out. Therefore we cannot add a timestamp prefix at loglevel STDOUT
        #       unless we manually keep track of when a new line starts.
        if self.timestampFmt:
            if record.levelno == logging.STDOUT:
                self._fmt = self.timestampFmt
                timeStamp = logging.Formatter.format(self, record)
                lines = record.getMessage().split('\n')
                if self._startLine:
                    lines[0] = timeStamp + lines[0]
                for i in range(1, len(lines)):
                    if len(lines[i]) != 0:
                        # Or put timeStamp instead of indentation?
                        lines[i] = len(timeStamp) * ' ' + lines[i]
                msg = '\n'.join(lines)
                self._startLine = (msg[-1:] == '\n')
                return msg
            else:
                self._fmt = self.timestampFmt + '%(message)s'
                self._startLine = True
                return logging.Formatter.format(self, record)
        else:
            # The code below assumes that redirected stdout always comes from
            # the root logger
            if record.name != 'root':
                self._fmt = '%(levelname)s:%(name)s: %(message)s'
            else:
                if record.levelno > logging.STDOUT or record.levelno == logging.DEBUG:
                    self._fmt = '%(levelname)s: %(message)s'
                else:
                    self._fmt = '%(message)s'
            return logging.Formatter.format(self, record)


class LevelFilter:

    """Logging filter to output messages depending on the log level."""

    def __init__(self, levelList, suppressFlag=True):
        """levelList is a list of log levels that should be
           either filtered out (suppressFlag=True, default) or pass
           the filter (suppressFlag=False)."""
        self.levelList = levelList
        self.suppressFlag = suppressFlag

    def filter(self, record):
        if self.suppressFlag:
            return 0 if record.levelno in self.levelList else 1
        else:
            return 1 if record.levelno in self.levelList else 0


class CmdHelper:

    """CmdHelper class to setup option parsing and logging.

    parseTool must be either optparse or argparse, and depending on
    it's value either an optparse.OptionParser or an
    argparse.ArgumentParser option parser will be
    instantiated. Initializes logging and redirects sys.stdout to go
    through logging if redirectStdOut is True.  If separateStdErr is
    True, everything except for standard output will be written to
    sys.stderr; otherwise sys.stdout is used for all console
    output. User arguments (argparse only) and options can be defined
    by either directly calling the OptionParser or ArgumentParser
    object via CmdHelper.parser, or using the utility methods
    CmdHelper.add_option and CmdHelper.add_argument."""

    def __init__(self, parseTool, version=None,
                 description=None, epilog=None,
                 redirectStdOut=True, separateStdErr=True, hasLogFile=True,
                 hasInteractive=True, hasBatch=False, hasDryRun=False,
                 logFile='', logSeparator=None, logTimestampFmt=None):
        if not parseTool in ('optparse','argparse'):
            raise ValueError('parseTool must be either "optparse" or "argparse"')
        self.parseTool = parseTool
        self.version = version
        self.description = description
        self.epilog = epilog
        self.redirectStdOut = redirectStdOut
        self.separateStdErr = separateStdErr
        self.hasLogFile = hasLogFile
        self.hasInteractive = hasInteractive
        self.hasBatch = hasBatch
        self.hasDryRun = hasDryRun
        self.logFile = logFile
        self.logSeparator = logSeparator
        self.logTimestampFmt = logTimestampFmt

        self.consoleHandler = None
        self.errorHandler = None
        self.fileHandler = None
        self.options = None
        self.args = None

        if self.parseTool == 'argparse':
            import argparse
            self.parser = argparse.ArgumentParser(description=description,
                                                  epilog=epilog,
                                                  formatter_class=argparse.RawTextHelpFormatter)
            self.add_argument('--version', action='version', version=version)
        else:
            import optparse
            self.parser = optparse.OptionParser(usage=description, version=version)
        if hasInteractive:
            self.add_option('-i', '--interactive', dest='interactive',
                                   action='store_true', default=False,
                                   help='enter interactive Python at completion')
        self.add_option('-v', '--verbose', dest='verbose',
                               action='store_true', default=False,
                               help='verbose output')
        self.add_option('', '--debug', dest='debug',
                               action='store_true', default=False,
                               help='debugging output')
        if hasDryRun:
            self.add_option('', '--dryrun', dest='dryrun',
                                   action='store_true', default=False,
                                   help='only show what would be done without --dryrun')
        if hasBatch:
            self.add_option('', '--batch', dest='batch',
                                   action='store_true', default=False,
                                   help='batch mode (skips confirmations)')
        if hasLogFile:
            self.add_option('', '--noscreen', dest='noscreen',
                                   action='store_true', default=False,
                                   help='disable logging output to screen')
            self.add_option('', '--logfile', dest='logfile',
                                   default=os.path.expandvars(logFile),
                                   help='write logging information to this file (default: %s)' % logFile)
            self.add_option('', '--loglevel', dest='loglevel',
                                   default='INFO',
                                   help='logging level for logfile (default: INFO, unless --debug is given)')
            self.add_option('', '--logseparator', dest='logseparator',
                                   default=logSeparator,
                                   help='message to write to logfile at beginning of new log')
            self.add_option('', '--logtimestampfmt', dest='logtimestampfmt',
                                   default=logTimestampFmt,
                                   help='timestamp format string (in logging formatter format)')

        # Root logger
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.NOTSET)

        # Handlers for console logging
        self.consoleHandler = MyStreamHandler(sys.stdout, True)  # Abort on console IOError (broken pipe etc)
        self.consoleHandler.setFormatter(ConsoleFormatter())
        self.consoleHandler.setLevel(logging.STDOUT)
        self.logger.addHandler(self.consoleHandler)
        if separateStdErr:
            self.consoleHandler.addFilter(LevelFilter([logging.STDOUT], False))
            self.errorHandler = MyStreamHandler(sys.stderr)
            self.errorHandler.setFormatter(ConsoleFormatter())
            self.errorHandler.addFilter(LevelFilter([logging.STDOUT], True))
            self.errorHandler.setLevel(logging.STDOUT)
            self.logger.addHandler(self.errorHandler)

        # Redirect stdout to logger if desired
        if redirectStdOut:
            sys.stdout = LogWriter(self.logger, logging.STDOUT)

    def add_option(self, *args, **kwargs):
        """Add optparse or argparse option depending on CmdHelper initialization."""
        if self.parseTool == 'argparse':
            if args and args[0] == '':   # no short option
                args = args[1:]
            return self.parser.add_argument(*args, **kwargs)
        else:
            return self.parser.add_option(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        """Add argparse argument."""
        return self.parser.add_argument(*args, **kwargs)

    def parse(self):
        """Parse options and handle defaults.

        When using OptionParser, returns tuple (options,args) of
        options and list of non-option command line arguments. When
        using ArgumentParser, returns Namespace object containing both
        options and arguments. In other words, parse() returns the
        same kind of that is returned by the corresponding parser's
        parse_args() function."""
        if self.parseTool == 'argparse':
            self.options = self.parser.parse_args()   # called options for backward compat.
        else:
            (self.options, self.args) = self.parser.parse_args()

        # If -i is given, make sure we go into interactive mode at the end
        try:
            if self.options.interactive:
                os.environ['PYTHONINSPECT'] = '1'
        except AttributeError:
            pass

        # Configure logging to file
        if getattr(self.options, 'logfile', None):
            self.fileHandler = MyStreamHandler(open(self.options.logfile, 'a'))
            self.fileHandler.setFormatter(FileFormatter(self.options.logtimestampfmt))
            if self.options.debug:
                self.fileHandler.setLevel(logging.DEBUG)
            else:
                try:
                    self.fileHandler.setLevel(int(self.options.loglevel))
                except ValueError:
                    try:
                        self.fileHandler.setLevel(
                            getattr(logging, self.options.loglevel.upper()))
                    except AttributeError:
                        error('illegal loglevel: %s' % self.options.loglevel)
            self.logger.addHandler(self.fileHandler)

        # Log command being executed (this goes only to self.fileHandler,
        # consoleHandler is still set to level STDOUT)
        info('')
        if self.options.logseparator:
            info(self.options.logseparator)
        #info('%s %s' % (time.asctime(), cmdLine()))
        info(cmdLine())
        info('')

        # Configure console logging level
        # NOTE: do this after logging command being executed, so that we don't get a logseparator
        #       or the command on the screen
        if self.options.verbose:
            self.consoleHandler.setLevel(logging.INFO)
        if self.options.debug:
            self.consoleHandler.setLevel(logging.DEBUG)
        if getattr(self.options, 'noscreen', False):
            self.consoleHandler.setLevel(9999)   # disable logging to consoleHandler
        if self.errorHandler:
            self.errorHandler.setLevel(logging.STDOUT)
            if self.options.verbose:
                self.errorHandler.setLevel(logging.INFO)
            if self.options.debug:
                self.errorHandler.setLevel(logging.DEBUG)
            if getattr(self.options, 'noscreen', False):
                self.errorHandler.setLevel(9999)   # disable logging to errorHandler

        if self.parseTool == 'argparse':
            return self.options
        else:
            return (self.options, self.args)


def cmdLine(useBasename=False):
    """Return full command line with any necessary quoting."""
    qargv = []
    cmdwords = list(sys.argv)
    if useBasename:
        cmdwords[0] = os.path.basename(cmdwords[0])
    for s in cmdwords:
        # any white space or special characters in word so we need quoting?
        if re.search(r'\s|\*|\?', s):
            if "'" in s:
                qargv.append('"%s"' % re.sub('"', "'", s))
            else:
                qargv.append("'%s'" % re.sub("'", '"', s))
        else:
            qargv.append(s)
    cmd = ' '.join(qargv)
    return cmd


def handleError(exception, debugFlag=False, abortFlag=True):
    """Error handling utility. Print more or less error information
       depending on debug flag. Unless abort is set False, exits with
       error code 1."""
    if isinstance(exception, CmdError) or not debugFlag:
        error(str(exception))
    else:
        import traceback
        traceback.print_exc()
        error(str(exception))   # or log complete traceback as well?
    if abortFlag:
        sys.exit(1)


#
# General utilities
#
def confirm(msg, acceptByDefault=False, exitCodeOnAbort=1, batch=False):
    """Get user confirmation or abort execution.

    Depending on acceptByDefault, the default answer (if user presses
    Return only), is to accept or abort.  " - are you sure [y] ?" or
    " - are you sure [n] ?" will be appended to msg, depending on the
    value of acceptByDefault. If the user does not accept,
    sys.exit(exitCodeOnAbort) will be called.  If batch is True,
    returns immediately."""
    if batch:
        return
    if acceptByDefault:
        msg += ' - are you sure [y] ? '
    else:
        msg += ' - are you sure [n] ? '
    while True:
        reply = raw_input(msg).lower()
        print
        if reply == '':
            reply = 'y' if acceptByDefault else 'n'
        if reply == 'y':
            return
        elif reply == 'n':
            error('Program execution aborted by user')
            sys.exit(exitCodeOnAbort)
        else:
            print "ERROR: Invalid reply - please enter either 'y' or 'n', or press just enter to accept default\n"


def run(cmd, printOutput=False,
        exceptionOnError=False, warningOnError=True,
        parseForRegEx=None, regExFlags=0,
        printOutputIfParsed=False, printErrorsIfParsed=False, exceptionIfParsed=False,
        dryrun=None):
    """Run cmd and return (status,output,parsedOutput).

    Run cmd and return the exit status and command output, unless
    dryrun is True. In that case the command is only logged but not
    executed.  cmd may either be a string, or a list of executable and
    args.  output is the full command output combined from stdout and
    stderr.  parsedOutput is the subset of the output that matches the
    regular expressions passed in parseForRegEx. If exceptionOnError
    is true and cmd exits with a non-zero status, an Exception is
    raised. If printOutputIfParsed or printErrorsIfParsed are set and
    there is parsedOutput, all output is printed or the matching lines
    are logged at the error level, respectively. The command being run
    is logged at the debug level."""
    if dryrun:
        debug('would run cmd: %s' % cmd)
        return (0, '', None)
    debug('running cmd: %s' % cmd)
    outputBuffer = []
    p = subprocess.Popen(cmd,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         shell=isinstance(cmd, str),
                         universal_newlines=True)
    for line in iter(p.stdout.readline, ""):
        outputBuffer.append(line.strip('\n'))
        if printOutput:
            sys.stdout.write(line)
    status = p.wait()
    output = '\n'.join(outputBuffer)
    if status and exceptionOnError:
        raise Exception('Error %s running command: %s: %s' %
                        (status, cmd, output))
    if status and warningOnError:
        warning('Error %s running command: %s: %s' % (status, cmd, output))
    if parseForRegEx:
        regex = re.compile(parseForRegEx, regExFlags)
        parsedOutput = '\n'.join([s for s in outputBuffer if regex.search(s)])
    else:
        parsedOutput = None
    if printOutputIfParsed and parsedOutput and not printOutput:
        print output
    if printErrorsIfParsed and parsedOutput:
        for l in parsedOutput.strip().split('\n'):
            error('found in command output: %s' % l)
    if exceptionIfParsed and parsedOutput:
        raise Exception('Errors found in command output - please check')
    return (status, output, parsedOutput)


#
# Test code
#
if __name__ == '__main__':
    cmdHelper = CmdHelper('argparse', __version__, 'Just an example', hasBatch=True, hasDryRun=True)
    cmdHelper.add_option('-x', '--example', dest='value', default=None, help='sample option')
    #(options, cmdargs) = c.parse()  # for optparse
    cmdargs = cmdHelper.parse() # for argparse
    debug("OK, let's start debugging")
    info('here we go')
    print 'Hello, world!'
    confirm('Testing')
    warning('note - missing newline; reply is not logged')
