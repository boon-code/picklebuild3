#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

from optparse import OptionParser
import sys
import os
import glob
import pfile
import targets


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
                    searching for a base-directory.
        """
        self._cfg = dict()
        self._real_init(cwd)
        self.loadConfig()
    
    def _find_base_dir(self, basedir='.'):
        
        for i in os.listdir(basedir):
            if i == _PCDIR:
                path = os.path.realpath(os.path.join(basedir, i))
                if os.path.isdir(path):
                    return basedir
        next_path = os.path.realpath(os.path.join(basedir, ".."))
        if next_path != basedir:
            return self._find_base_dir(basedir=next_path)
    
    def _real_init(self, cwd):
        bd = self._find_base_dir(cwd)
        if bd is not None:
            self.base_dir = os.path.realpath(bd)
            self.config_dir = os.path.join(self.base_dir, _PCDIR)
        else:
            self.base_dir = None
            self.config_dir = None
        self.source = "src/"
        self.dest = "out/"
        self._targets = None
    
    def initialize(self, cwd, obj):
        
        if self.isInitialized():
            return False
        else:
            self._real_init(cwd)
            self.updateSettings(obj)
    
    def isInitialized(self):
        return (self.config_dir is not None)
    
    def updateSettings(self, obj):
        
        if self.isInitialized():
            try:
                self.source = os.path.relpath(obj.src, self.base_dir)
                self.dest = os.path.relpath(obj.dst, self.base_dir)                
            except AttributeError as e:
                print("This shouldn't happen!!")
                raise
            self.saveConfig()
    
    def _update_targets(self):
        src = os.path.normpath(os.path.join(self.base_dir, self.source))
        self._targets = targets.TargetTree(src)
        if 'tgl' not in self._cfg:
            self._cfg['tgl'] = list()
        for i in self._cfg['tgl']:
            path = os.path.join(src, i)
            self._targets.add(path)
    
    def addTarget(self, path):
        if self.isConfigured():
            self._targets.add(path)
    
    def rmTarget(self, path):
        if self.isConfigured():
            self._targets.remove(path)
    
    def isConfigured(self):
        
        v = ('src', 'dst')
        for i in v:
            if i not in self._cfg:
                return False
        return True
    
    def saveConfig(self):
        
        if self.isInitialized():
            path = os.path.join(self.config_dir, _PCMAIN)
            self._cfg['src'] = self.source
            self._cfg['dst'] = self.dest
            self._cfg['tgl'] = list()
            for node in self._targets.iterDirs():
                for i in node.iterFiles():
                    self._cfg['tgl'].append(i)
            pfile.saveControlFile(path, self._cfg)
    
    def loadConfig(self):
        
        if self.isInitialized():
            path = os.path.join(self.config_dir, _PCMAIN)
            if os.path.isfile(path):
                cfg = pfile.loadControlFile(path)
                if isinstance(cfg, dict):
                    self._cfg = cfg
            if self.isConfigured():
                self.source = self._cfg['src']
                self.dest = self._cfg['dst']
            self._update_targets()

def _expand(path):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return glob.iglob(path)

def _expand_all(args):
    for i in args:
        for j in _expand(i):
            yield j


def add(args):
    parser = OptionParser(usage="usage: %prog add [options] files")
    options, args = parser.parse_args(args)
    
    if len(args) < 1:
        parser.print_help(file=sys.stderr)
    else:
        cfg = MainConfig(os.getcwd())
        for i in _expand_all(args):
            cfg.addTarget(i)
        cfg.saveConfig()
        cfg._targets.dumpTree()

def rm(args):
    parser = OptionParser(usage="usage: %prog rm [options] files")
    options, args = parser.parse_args(args)
    
    if len(args) < 1:
        parser.print_help(file=sys.stderr)
    else:
        cfg = MainConfig(os.getcwd())
        for i in _expand_all(args):
            cfg.rmTarget(i)
        cfg.saveConfig()
        cfg._targets.dumpTree()

def setup(args):
    
    parser = OptionParser(usage="usage: %prog setup [options]")
    parser.add_option("-s", "--source-dir", default="./src/"
     , help="sets source directory (default is %default)"
     , dest="src")
    parser.add_option("-d", "--destination-dir", default="./out/"
     , help="sets output directory (default is %default)"
     , dest="dst")
    parser.add_option("-j", "--just-show", action="store_true"
     , help="Print current configuartion without changing anything"
     , default=False, dest="show")
    options, args = parser.parse_args(args)
    
    cfg = MainConfig(os.getcwd())
    
    if options.show:
        if cfg.isInitialized():
            print("Found initialized pconfig dir (%s)"
             % cfg.config_dir)
            if cfg.isConfigured():
                print("Everything properly set up.")
            else:
                print("Not yet set up.")
        else:
            print("Couldn't find root directory, use 'setup'")
    else:
        if cfg.isInitialized():
            print("update directory")
            cfg.updateSettings(options)
        else:
            os.mkdir(_PCDIR)
            cfg.initialize(os.getcwd(), options)


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
        if args[1] == 'setup':
            return setup(args[2:])
        elif args[1] == 'add':
            return add(args[2:])
        elif args[1] == 'rm':
            return rm(args[2:])
        elif args[1] == 'make':
            pass
        elif args[1] == 'cfg':
            pass
    return showMain(args)


if __name__ == '__main__':
    main(sys.argv)
