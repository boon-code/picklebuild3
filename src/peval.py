#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module is about inline python code evaluation.

This module is based on an old one I used in my old buildsystem.
I introduced a new class, PyParser. This class replaces the parseData
method. It's a bit more flexible, which I needed to calculate the
current line number if an error occurred (This should be very
helpful to find errors in configure scripts).
"""

import sys
import os
import re
import traceback
import logging


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


class CodeEvaluationError(EvalException):
    """This exception will be raised, if evaluated code fails.
    
    Since this module executes user written code, it's very
    likely that there are errors in the code and it fails.
    This exception should indicate where the error happend
    to give feedback to the user.
    """
    
    def __init__(self, name, line, *args):
        """Initializes a new instance.
        
        :param name: Name of the file that caused the error.
        :param line: Line number where the error occurred.
        :param args: Other arguments that will be passed to
                     base.
        """
        EvalException.__init__(self, *args)
        self.line = line
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
        self._env = env
        self._name = name
        self._log = logging.getLogger(_LOGGER_NAME)
        
        # TRICKEY: I start counting at 0 (see _eval_data).
        self._curr_line = 0
    
    def _eval_data(self, code):
        """Evaluates an inline python code block.
        
        :param code: The source code that this method will
                     execute.
        """
        try:
            exec(code, self._env, self._env)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            tb = sys.exc_info()[2]
            tb = tb.tb_next
            
            # TRICKEY: Since self._curr_line starts with 0
            #          We can simple add both line numbers.
            ln = self._curr_line + tb.tb_lineno
            
            errtxt = ("Script Error: name: '%s', line '%d'"
             % (self._name, ln))
            self._log.exception(errtxt)
            raise CodeEvaluationError(self._name, ln, *e.args) from e 
    
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
        self._env['echo'] = echo_obj.echo
        self._env['put'] = echo_obj.echo_nl
        self._env['sput'] = echo_obj.str_echo_nl
        self._env['secho'] = echo_obj.str_echo
        
        tag = False
        code = ''
        found = True
        self._curr_line = 0
        
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
                    raise MissingClosingTagError(self._name
                     , self._curr_line)
        
        if len(data) > 0:
            self._dst.write(data)
            self._dst.flush()
