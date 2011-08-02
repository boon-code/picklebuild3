#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

from optparse import OptionParser
import sys
import os
import collections
import pfile

VERSION = 'v0.0.1'

_PCDIR = '.pconfig'
_PCMAIN = 'main.jso'
# Used by _find_cfg_dir. It's the name of the config dir.


class MainConfig(object):
    """Covers basic config.
    
    This class represents the current config. This includes
    source directory, output directory, ... 
    """
    
    def __init__(self, cwd):
        """This creates a new instance.
        
        @param cwd: The current working directory to start
                    searching for a config-directory.
        """
        self.config_dir = self._find_cfg_dir(cwd)
        self.cfg = dict()
        self.loadConfig()
    
    def _find_cfg_dir(self, basedir='.'):
        
        for i in os.listdir(basedir):
            if i == _PCDIR:
                path = os.path.realpath(os.path.join(basedir, i))
                if os.path.isdir(path):
                    return path
        next_path = os.path.realpath(os.path.join(basedir, ".."))
        if next_path != basedir:
            return self._find_cfg_dir(basedir=next_path)
    
    def initialize(self, cwd):
        
        if self.isInitialized():
            return False
        else:
            self.config_dir = self._find_cfg_dir(cwd)
            self.cfg = dict()
            self.saveConfig()
    
    def isInitialized(self):
        return (self.config_dir is not None)
    
    def updatePaths(self, obj):
        
        try:
            self.cfg['src'] = obj.src
            self.cfg['dst'] = obj.dst
            self.saveConfig()
        except AttributeError as e:
            print("This shouldn't happen!!")
            raise
    
    def isConfigured(self):
        
        v = ('src', 'dst', 'targets')
        for i in v:
            if i not in self.cfg:
                return False
        return True
    
    def saveConfig(self):
        
        if self.isInitialized():
            path = os.path.join(self.config_dir, _PCMAIN)
            pfile.saveControlFile(path, self.cfg)
    
    def loadConfig(self):
        
        if self.isInitialized():
            path = os.path.join(self.config_dir, _PCMAIN)
            if os.path.isfile(path):
                cfg = pfile.loadControlFile(path)
                if isinstance(cfg, dict):
                    self.cfg = cfg


def add(args):
    parser = OptionParser(usage="usage: %prog add [options] files")
    options, args = parser.parse_args(args)
    
    #

def init(args):
    
    parser = OptionParser(usage="usage: %prog init [options]")
    parser.add_option("-s", "--source-dir", default="./src/"
     , help="sets source directory (default is %default)"
     , dest="src")
    parser.add_option("-d", "--destination-dir", default="./out/"
     , help="sets output directory (default is %default)"
     , dest="dst")
    options, args = parser.parse_args(args)
    
    cfg = MainConfig(os.getcwd())
    
    if cfg.isInitialized():
        print("update directory")
        cfg.updatePaths(options)
    else:
        os.mkdir(_PCDIR)
        cfg.initialize(os.getcwd())
        cfg.updatePaths(options)


def showMain(args):
    parser = OptionParser(usage="usage: %prog cmd")
    parser.add_option("-V", "--version", action="store_true"
         , help="prints current version to stdout")
    parser.set_defaults(verbose=False, version=False)
    options, args = parser.parse_args(args)
    
    if options.version:
        print("pbuild version %s" % VERSION)
    else:
        parser.print_help(file=sys.stderr)


def main(args):
    
    if len(args) >= 2:
        if args[1] == 'init':
            return init(args[2:])
        elif args[1] == 'add':
            return add(args[2:])
        elif args[1] == 'rm':
            pass
        elif args[1] == 'make':
            pass
        elif args[1] == 'cfg':
            pass
    return showMain(args)


if __name__ == '__main__':
    main(sys.argv)
