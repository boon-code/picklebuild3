#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import split, join, normpath
import sys
import unittest

class TestExecEnvironment(unittest.TestCase):
    
    def setUp(self):
        env = {'__builtins__' : __builtins__}
        self._eval = ExecEnvironment(env)
    
    def test_valid1(self):
        code = "a = 7\nb = 3\nc = 10"
        e = self._eval
        e(code)
        self.assertTrue('a' in e.env)
        self.assertTrue('b' in e.env)
        self.assertTrue('c' in e.env)
    
    def test_invalid1(self):
        code = "askfjls"
        e = self._eval
        try:
            e(code)
        except CodeEvalError as e:
            self.assertTrue(isinstance(e.__cause__, NameError))
            self.assertTrue(e.line == 1)
    
    def tearDown(self):
        self._eval = None


if __name__ == '__main__':
    base = split(sys.argv[0])[0]
    path = normpath(join(base, "../src/"))
    sys.path.insert(0, path)
    from peval import ExecEnvironment, CodeEvalError
    unittest.main()
