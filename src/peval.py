#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module is about inline python code evaluation.

This module is based on an old one I used in my old buildsystem.
I introduced a new class, PyParser. This class replaces the parseData
method. It's a bit more flexible, which I needed to calculate the
current line number if an error occurred (This should be very
helpful to find errors in source code using inline python code tags).
"""

from functools import partial
import sys
import os
import re
import imp
import traceback
import logging
import builtins
from pbasic import NotYetWorkingWarning


__author__ = 'Manuel Huber'
__copyright__ = "Copyright (c) 2011 Manuel Huber."
__license__ = 'GPLv3'
__docformat__ = "restructuredtext en"

_START_TAG = "<?"
_END_TAG = "?>"
_CODE_RE = re.compile("^<\\?\\s*py:")
_LOGGER_NAME = 'eval'


class EvalException(Exception):
    """This is the base-exception for this module.
    
    All Exception have to be derived from this.
    """
    pass


class CodeEvalError(EvalException):
    """This exception will be raised, if evaluated code fails.
    
    Since this module executes user written code, it's very
    likely that there are errors in the code and it fails.
    This exception should indicate where the error happend
    to give feedback to the user.
    """
    
    def __init__(self, name, line, args, cause=None):
        """Initializes a new instance.
        
        :param name:    Name of the file that caused the error.
        :param line:    Line number where the error occurred.
        :param args:    Other arguments that will be passed to
                        base.
        :keyword cause: The line of code that caused the error
                        or None.
        """
        EvalException.__init__(self, *args)
        self.line = line
        self.name = name
        self.cause = cause


class NotAllowedError(EvalException):
    """Will be raised on forbidden access of builtin methods.
    
    This exception will be used by ExecEnvironment to indicate
    that some user code tried to access builtins that are
    forbidden (because they could be dangerouse).
    """
    
    def __init__(self, name, *args):
        """Initializes a new instance.
        
        :param name: Name of the element that the user code had 
                     tried to access.
        :param args: Will be passed to base class.
        """
        text = "Tried to access builtin '%s'" % name
        EvalException.__init__(self, text, *args)
        self.name = name


class MissingClosingTagError(EvalException):
    """This exception will be raised on missing closeing tags.
    
    If the file that is about to execute contains an inline
    python code start tag but no corresponding end tag could be
    found, this exception will be raised.
    """
    
    def __init__(self, name, line, *args):
        """Initializes a new instance.
        
        :param name: Name of the file that produced the error.
        :param line: Line number of starting block.
        :param args: Additional arguments that will be passed
                     to base exception class.
        """
        EvalException.__init__(self, *args)
        self.line = line
        self.name = name


def _cpp_escape(value):
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    return value


class EchoHelper(object):
    """This class offers methods to write text to an open file.
    
    This class will be used by the *parseData* function of this
    module. It's not indent to be used by other modules
    (though it can be used), it only offers basic methods
    that will be offered to the inline code.
    """
    
    def __init__(self, dst):
        """Initializes a new instance.
        
        :param dst: A file like object that represents the file
                    to write to.
        """
        self._dst = dst
    
    def _list_echo(self, text, pre=None, post=None):
        if not (pre is None):
            self._dst.write(str(pre))
        if len(text) > 0:
            for element in text:
                self._dst.write(str(element))
        if not (post is None):
            self._dst.write(str(post))
        self._dst.flush()
    
    def echo(self, *text):
        self._list_echo(text)
    
    def echo_nl(self, *text):
        self._list_echo(text, post='\n')
    
    def str_echo(self, *text):
        text = [_cpp_escape(str(i)) for i in text]
        self._list_echo(text, pre='"', post='"')
    
    def str_echo_nl(self, *text):
        text = [_cpp_escape(str(i)) for i in text]
        self._list_echo(text, pre='"', post='"\n')


class ExceptionRaiser(object):
    
    def __init__(self, exc, *args, **kargs):
        """Initializes a new instance.
        
        :param exc:   Exception class that shall be used
        :param args:  Arguments, passed to the instance of 
                      the exception class, that will be created
                      on call.
        :param kargs: Keyword arguments that will be passed to
                      the created exception on call.
        """
        self._exc_class = exc
        self._args = args
        self._kargs = kargs
    
    def __call__(self, *args, **kargs):
        """If the object gets called, raise predefined exception.
        
        :param args:  Take arguments.
        :param kargs: Take keyword arguments.
        """
        raise self._exc_class(*self._args, **self._kargs)


class ExecBuiltins(object):
    """This class emulates the *builtin* module.
    
    It contains a blacklist of all objects that
    shall not be accessed.
    """
    
    blacklist = ('__debug__', '__import__', 'eval', 'exec'
     , 'open', 'compile')
    
    def __init__(self, **changes):
        """Initializes a new instance.
        
        At startup, all none-blacklisted member of *builtins*
        module will be copied to the *self._wl* dictionary
        (whitelist).
        
        :param changes: All keys in that dict will be interpreted
                        as *builtins* members and will be
                        changed to the value of the key.
        """
        bl = ExecBuiltins.blacklist
        wl = dict()
        self._wl = wl
        for i in dir(builtins):
            if i not in bl:
                wl[i] = getattr(builtins, i)
        for (k, v) in changes.items():
            wl[k] = v
    
    def __getattribute__(self, attr_name):
        """Access method used by objects to retrieve a member.
        
        This method has been overridden to hide all members
        except members from *builtins* that don't show on the
        blacklist.
        
        :raise NotAllowedError: If it's tried to access a member
                                of *builtins* that is on the 
                                blacklist.
        :raise AttributeError:  If a member is tried to access
                                that is hidden or doesn't even
                                exist.
        
        :param attr_name:       The attribute name that has been
                                tried to beeing accessed.
        """
        wl = object.__getattribute__(self, '_wl')
        bl = ExecBuiltins.blacklist
        if attr_name in wl:
            return wl[attr_name]
        elif attr_name in bl:
            raise NotAllowedError(attr_name, "Execution of builtin\
not allowed.")
        else:
            class_ = object.__getattribute__(self, '__class__')
            raise AttributeError(
                "'%s' doesn't have an attribute named '%s'"
                % (str(class_.__name__), attr_name))
    
    def __dir__(self):
        wl = object.__getattribute__(self, '_wl')
        return list(wl.keys())


class ExecEnvironment(object):
    """This class can be used to evaluate code
    
    I will try to make this method as secure as possible as well
    as helpful for the user to find errors.
    """
    
    blacklist = ('__debug__', '__import__', 'eval', 'exec'
     , 'open', 'compile')
    
    def __init__(self, env=dict(), ovr_builtins=False
     , name="<string>"):
        """Initializes a new instance.
        
        :keyword env:          An environment dictionary that 
                               should cover all variables that are
                               needed by the executed code. The 
                               environment can be changed by the 
                               code (and subsequent calls will use 
                               the modified version of env).
        :keyword ovr_builtins: The override-buitlins flag controls,
                               if this class will use a supplied
                               *__builtins__* version, or use it's
                               own. If set to True, the built-in
                               version will be used.
        :keyword name:         *name* will be used by compile
                               and can be used to add context
                               what is about to be executed
                               (A file, user input, etc...).
                               Default is '<string>'.
        """
        self.env = env
        self.name = name
        self._log = logging.getLogger(_LOGGER_NAME)
        
        bi = self.env.pop('__builtins__', None)
        
        if ovr_builtins:
            # Not yet finished!!!
            # This is not yet safe
            bi = imp.new_module("exbuiltins")
            setattr(bi, 'getattr', self._get_attr)
        elif bi is None:
            bi = builtins
        self.env['__builtins__'] = bi
        self.env['getattr'] = self._get_attr
    
    def _get_attr(self, attr_name):
        
        if attr_name in self.blacklist:
            raise NotAllowedError(the_member_name, "Not allowed")
        else:
            return builtins.getattr(attr_name)
    
    def __call__(self, data, add_ln=0):
        """Executes the given string as python code.
        
        :param data:     Data that will be executed.
        :keyword add_ln: This number will be added to the line
                          number, if an error occurres.
        """
        try:
            code = compile(data, self.name, 'exec')
        except (KeyboardInterrupt, SystemExit):
            raise
        except SyntaxError as e:
            tb = sys.exc_info()[2]
            ln = tb.tb_lineno + add_ln
            self._log.debug("Error while trying to compile user-code.")
            raise CodeEvalError(self.name, ln, e.args
             , cause=e.text) from e
        
        try:
            exec(code, self.env, self.env)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            tb = sys.exc_info()[2]
            if tb.tb_next is None:
                raise
            tb = tb.tb_next
            ln = tb.tb_lineno + add_ln
            self._log.debug("Error while trying to execute user-code.")
            raise CodeEvalError(self.name, ln, e.args
             , cause=str(e)) from e


class PyParser(object):
    """This class is used to execute inline python code.
    
    It parses a string and writes the resulting file
    to a stream.
    """
    
    def __init__(self, dst, env, name="<noname>"):
        """Initializes a new instance.
        
        :param dst:    The destination stream. All data will be written
                       to this stream.
        :param env:    The environment which will be used to execute
                       the inline python code.
        :keyword name: Name to idientify the file that is about to
                       be executed.
        """
        self._dst = dst
        self._name = name
        self._log = logging.getLogger(_LOGGER_NAME)
        self._curr_line = 1
        self._eval = ExecEnvironment(env, name=name)
    
    def _eval_data(self, code):
        """Evaluates an inline python code block.
        
        :param code: The source code that this method will
                     execute.
        """
        self._eval(code, add_ln=(self._curr_line - 1))
    
    def _add_line_count(self, chunk):
        """Counts newline characters and adds them to current.
        
        This method just counts all newline characters in *chunk*
        and adds the number to the current line number 
        *self._curr_line*.
        
        :param chunk: The string to search for newline characters.
        """
        self._curr_line += chunk.count('\n')
    
    def parseString(self, data):
        """Parses a string and executes all inline code.
        
        All none inline code from *data* will just be copied to 
        self._dst (see constructor). All python inline tags will be
        replaced by their output.
        
        :param data: Data that will be parsed and executed.
        :type data: string
        """
        echo_obj = EchoHelper(self._dst)
        self._eval.env['echo'] = echo_obj.echo
        self._eval.env['put'] = echo_obj.echo_nl
        self._eval.env['sput'] = echo_obj.str_echo_nl
        self._eval.env['secho'] = echo_obj.str_echo
        
        tag = False
        code = ''
        found = True
        self._curr_line = 1
        
        while found:
            if not tag:
                start_pos = data.find(_START_TAG)
                if start_pos >= 0:
                    chunk = data[0:start_pos]
                    if len(chunk) > 0:
                        self._add_line_count(chunk)
                        self._dst.write(chunk)
                    tag = True
                    data = data[start_pos:]
                    code_match = _CODE_RE.search(data)
                    if not (code_match is None):
                        code = ''
                        data = data[code_match.end():]
                else:
                    found = False
            
            if tag:
                end_pos = data.find(_END_TAG)
                if end_pos >= 0:
                    tag = False
                    if not (code_match is None):
                        code = data[0:end_pos]
                        self._eval_data(code)
                        self._add_line_count(code)
                        end_pos += len(_END_TAG)
                        data = data[end_pos:]
                    else:
                        self._log.warning("Unknown tag (~line '%d')."
                         % self._curr_line)
                else:
                    found = False
                    self._log.error("No closing ?>, line '%d':"
                     % self._curr_line)
                    raise MissingClosingTagError(self._eval.name
                     , self._curr_line)
        
        if len(data) > 0:
            self._dst.write(data)
            self._dst.flush()
