#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re

_START_TAG = "<?"
_END_TAG = "?>"
_CODE_RE = re.compile("^<\\?\\s*py:")


def _cpp_escape(value):
    value = value.replace('\\', '\\\\')
    value = value.replace('"', '\\"')
    return value


def _eval_data(code, env):
    
    try:
        exec(code, env, env)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
    except Exception:
        sys.stderr.write(traceback.format_exc())
        sys.exit(1)


class EchoHelper(object):
    
    def __init__(self, dst):
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


def parseData(data, dst, env):
    
    echo_obj = EchoHelper(dst)
    env['echo'] = echo_obj.echo
    env['put'] = echo_obj.echo_nl
    env['sput'] = echo_obj.str_echo_nl
    env['secho'] = echo_obj.str_echo
    
    tag = False
    code = ''
    found = True
    
    while found:
        if not tag:
            start_pos = data.find(_START_TAG)
            if start_pos >= 0:
                if len(data[0:start_pos]) > 0:
                    dst.write(data[0:start_pos])
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
                    _eval_data(code, env)
                    end_pos += len(_END_TAG)
                    data = data[end_pos:]
                else:
                    sys.stderr.write("unknown tag...")
            else:
                found = False
                sys.stderr.write("didn't find '?>'")
                sys.exit()
    
    if len(data) > 0:
        dst.write(data)
        dst.flush()
