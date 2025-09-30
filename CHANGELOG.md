# Release history (latest release first)

## v0.4.0
- remove Python 2.7 support, now requiring Python 3.6 or later
- bug fix for logging.Formatter change from _fmt to _style._fmt (thanks to Matt Kramer)
- convert README and CHANGLOG files to Markdown
- add .gitignore file
- update Makefile and switch to twine for uploading to PyPI
- add uv lock file
- update history handling in interactive Python to use new REPL in Python 3.13

## v0.3.1
- add --commit option as an orthogonal alternative to --dryrun
- reinstate fix for UnicodeEncodeError in Python 2

## v0.3.0
- support both Python 2.7 and Python 3.x
- some code cleanup

## v0.2.11
- add utility to enable history for interactive use with -i option

## v0.2.10
v0.2.9
- fix issue with logging messages with non-ASCII characters when redirecting output or logging to files

## v0.2.8
- add abort utility to abort program after issuing error message

## v0.2.7
- add example.py
- misc internal improvements

## v0.2.6
- reset PYTHONINSPECT before invoking subprocess in run() so python commands terminate properly

## v0.2.5
- add options to e-mail log messages
- option to send e-mail only if message at trigger severity (or above) is logged
- improve documentation

## v0.2.4
- improve examples

## v0.2.3
- allow unicode in cmd strings
- add Makefile to simplify uploading to PyPI
- add debugFlag to handleError example

## v0.2.2
- improve message formatting
- improve documentation

## v0.2.1
- initial public version
