#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

from optparse import OptionParser
import sys
import os
import glob
from pbgui_imp import Pbgui
import pfile
import targets
import pmodules
import cfgcontrol


__author__ = 'Manuel Huber'
__copyright__ = "Copyright (c) 2011 Manuel Huber."
__license__ = 'GPLv3'
__version__ = '0.0.1'
__docformat__ = "restructuredtext en"


_VERSION = '%prog v' + __version__
# Version string, used by optparse module.

_PCDIR = '.pconfig'
# Used by _find_cfg_dir. It's the name of the config dir.

_PCMAIN = 'main.jso'
_PC_CCF = 'current-config.jso'
_DEFAULT_SRC = './src/'
_DEFAULT_DST = './out/'

_CMD_USAGE = """Usage: %prog `cmd`

picklebuild commands:
  setup:  Initializes a new picklebuild project. Can also be used to
          update source and destination path.
  add:    Add a file to the index (has to be setup first).
  rm:     Removes a file from index.
  status: Shows current status (Index).
  cfg:    Shows the configure window. Normally, the current config 
          will be used. If you press ok, it will be saved to current 
          config, if you press cancle it won't be saved.
  make:   This command will finally generate output."""

_CMD_DESC = """You can always use the --help option on each
command to get a more specific help."""


class SourceNotFoundError(Exception):
    
    def __init__(self, path, *args):
        self.path = path


class NotProperlyConfiguredError(Exception):
    
    def __init__(self, src, dst, tgets, *args):
        error_src = list()
        if src is None:
            error_src.append("Source not properly set.")
        if dst is None:
            error_src.append("Destination not properly set.")
        if tgets is None:
            error_src.append("Targets not set up correctly.")
        self.error_source = "\n".join(error_src)


def _get_nn(value, default=None):
    """Return not None (if possible).
    
    :param value:   Value that will be returned (if not None).
    :param default: Value that will be returned if value is None.
    :returns:       Returns value unless value is None. If so
                    returns default.
    """
    if value is None:
        return default
    else:
        return value


class MainConfig(object):
    """Covers basic configuartion.
    
    This class represents the current configuartion. This includes
    source directory, output directory, ... 
    """
    
    def __init__(self, cwd, autoload=True, failinpc=False):
        """This creates a new instance.
        
        :param cwd:      The current working directory to start
                         searching for a base-directory.
        :param autoload: If set, loadConfig will automatically 
                         be called.
        :param failinpc: Fail if not properly configured.
                         This automatically enables autoload.
        """
        self._real_init(cwd)
        if autoload or failinpc:
            self.loadConfig()
        if failinpc and (not self.isProperlyConfigured()):
            raise NotProperlyConfiguredError(self.source, self.dest
                 , self.targets, "Not properly set up.")
    
    def _find_base_dir(self, basedir='.'):
        """This method searchs for a .pconfig directory
        
        It just checks each directory and if there is no .pconfig
        directory, it's parent directory will be searched (aso).
        
        :param basedir: Current directory that will be searched.
        :returns:       Returns path to the next pconfig directory
                        or None if there is no pb project.
        """
        for i in os.listdir(basedir):
            if i == _PCDIR:
                path = os.path.realpath(os.path.join(basedir, i))
                if os.path.isdir(path):
                    return basedir
        next_path = os.path.realpath(os.path.join(basedir, ".."))
        if next_path != basedir:
            return self._find_base_dir(basedir=next_path)
    
    def _real_init(self, cwd):
        """Really initializes this object.
        
        :param cwd: Searching will start in this directory. Normally
                    this should be the current working directory.
        """
        self.base_dir = None
        self.config_dir = None
        self.targets = None
        self.source = None
        self.dest = None
        
        bd = self._find_base_dir(cwd)
        if bd is not None:
            self.base_dir = os.path.realpath(bd)
            self.config_dir = os.path.join(self.base_dir, _PCDIR)
    
    def foundConfig(self):
        """Returns if a pb project could be found.
        
        That means, a .pconfig directory could be found and it's
        path will be stored to *config_dir* member, while the
        root path (*config_dir*/..) will be saved to *base_dir*
        member.
        
        :returns: True if basic paths are set up, else False.
        """
        return (None not in (self.base_dir, self.config_dir))
    
    def isProperlyConfigured(self):
        """Returns, if all parameters are properly set up.
        
        *source*, *dest*, and *targets* members have to be set up
        since these members will be used by other parts of this 
        software. If these members are set, the configuration is valid
        and all subcommands should work. If not, the `setup` command
        should be used to initialize the project.
        
        :returns: True if proper configured, else False.
        """
        return (None not in (self.source, self.dest, self.targets))
    
    def fullSource(self):
        """Returns a full path to the source directory.
        
        Note that this method will fail if this object is not 
        initialized and properly configured.
        
        :returns: Full path to the source dirctory.
        """
        src = os.path.join(self.base_dir, self.source)
        return os.path.normpath(src)
    
    def fullDestination(self):
        """Returns the full path to the destination directory.
        
        Note that this method will fail if this object is not
        initialized and properly configured.
        
        :returns: Full path to the destination directory.
        """
        dst = os.path.join(self.base_dir, self.dest)
        return os.path.normpath(dst)
    
    def setupFromObject(self, obj, cwd=None):
        
        cfg = dict()
        try:
            cfg['src'] = obj.src
            cfg['dst'] = obj.dst
        except AttributeError:
            print("bad attribute error")
            raise
        return self.setup(cfg, cwd=cwd)
    
    def setup(self, cfg, cwd=None, fail=True):
        
        if not self.foundConfig():
            if cwd is None:
                cwd = os.getcwd()
            os.mkdir(_PCDIR)
            self.source = _DEFAULT_SRC
            self.dest = _DEFAULT_DST
            self._real_init(cwd)
        
        if self.foundConfig():
            tgl = list()
            if self.targets is not None:
                tgl = list(self.targets.iterNames())
            
            self.targets = None
            self.source = _get_nn(cfg.pop('src', None)
                 , default=self.source)
            self.dest = _get_nn(cfg.pop('dst', None)
                 , default=self.dest)
            
            if None in (self.source, self.dest):
                if fail:
                    raise Exception("Not setup correctly")
                else:
                    print("Couldn't setup correctly")
                    return
            
            if not os.path.isdir(self.fullSource()):
                if fail:
                    raise SourceNotFoundError(self.fullSource()
                        , "Couldn't find source")
                else:
                    return
            
            self.targets = targets.TargetTree(self.fullSource())
            if 'tgl' in cfg:
                # Replace tgl if it has been set in cfg dict.
                tgl = cfg['tgl']
            for i in tgl:
                self.targets.add(i, relative=True)
        else:
            #TODO: Exception!
            raise Exception("Couldn't setup config dir")
    
    def addTarget(self, path):
        if self.isProperlyConfigured():
            self.targets.add(os.path.realpath(path))
    
    def rmTarget(self, path):
        if self.isProperlyConfigured():
            self.targets.remove(os.path.realpath(path))
    
    def saveConfig(self, leave_tgl=False):
        
        if self.isProperlyConfigured():
            path = os.path.join(self.config_dir, _PCMAIN)
            cfg = dict()
            cfg['src'] = self.source
            cfg['dst'] = self.dest
            if not leave_tgl:
                cfg['tgl'] = list(self.targets.iterNames())
            else:
                old = self._load_config()
                if old is None:
                    cfg['tgl'] = list()
                else:
                    cfg['tgl'] = old.pop('tgl', list())
            pfile.saveControlFile(path, cfg)
    
    def _load_config(self):
        if self.foundConfig():
            path = os.path.join(self.config_dir, _PCMAIN)
            cfg = pfile.loadControlFile(path)
            if isinstance(cfg, dict):
                return cfg
    
    def loadConfig(self, fail=True):
        
        cfg = self._load_config()
        if cfg is not None:
            self.setup(cfg, fail=fail)


def _expand(path):
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)
    return glob.iglob(path)


def _expand_all(args):
    for i in args:
        empty=True
        for j in _expand(i):
            empty=False
            yield j
        if empty:
            yield i


def add(args):
    parser = OptionParser(usage="usage: %prog add [options] files"
     , version=_VERSION)
    options, args = parser.parse_args(args)
    
    if len(args) < 1:
        parser.print_help(file=sys.stderr)
    else:
        cfg = MainConfig(os.getcwd(), failinpc=True)
        for i in _expand_all(args):
            cfg.addTarget(i)
        cfg.saveConfig()
        cfg.targets.dumpTree()

def rm(args):
    parser = OptionParser(usage="usage: %prog rm [options] files"
     , version=_VERSION)
    options, args = parser.parse_args(args)
    
    if len(args) < 1:
        parser.print_help(file=sys.stderr)
    else:
        cfg = MainConfig(os.getcwd(), failinpc=True)
        for i in _expand_all(args):
            cfg.rmTarget(i)
        cfg.saveConfig()
        cfg.targets.dumpTree()

def setup(args):
    
    parser = OptionParser(usage="usage: %prog setup [options]"
     , version=_VERSION)
    parser.add_option("-s", "--source-dir", dest="src"
     , help="sets source directory (default is %s" % _DEFAULT_SRC)
    parser.add_option("-d", "--destination-dir", dest="dst"
     , help="sets output directory (default is %s)" % _DEFAULT_DST)
    parser.add_option("-i", "--info", action="store_true"
     , help="Print current configuartion without changing anything"
     , default=False, dest="show")
    parser.add_option("-o", "--override", action="store_true"
     , help="This flag has to be attached, to enable change directory"
     , default=False)
    options, args = parser.parse_args(args)
    
    cfg = MainConfig(os.getcwd(), autoload=False)
    
    dir_nn = (options.src is not None) or (options.dst is not None)
    
    if cfg.foundConfig():
        if options.show:
            print("Found initialized pconfig dir (%s)"
             % cfg.config_dir)
            cfg.loadConfig(fail=False)
            if cfg.isProperlyConfigured():
                print("source: ", cfg.source)
                print("dest: ", cfg.dest)
                print("Everything properly set up.")
            else:
                print("source: ", cfg.source)
                print("dest: ", cfg.dest)
                print("Not correctly set up.")
        elif dir_nn and options.override:
            cfg.loadConfig(fail=False)
            cfg.setupFromObject(options)
            cfg.saveConfig(leave_tgl=True)
        elif dir_nn and (not options.override):
            print("you have to add --override to reconfigure.")
        else:
            print("This already is a pickleconfig project.")
    else:
        cfg.setupFromObject(options)
        cfg.saveConfig()


def status(args):
    parser = OptionParser(usage="usage: %prog status"
     , version=_VERSION)
    options, args = parser.parse_args(args)
    
    cfg = MainConfig(os.getcwd(), failinpc=True)
    cfg.targets.dumpTree()


def configure(args):
    parser = OptionParser(usage="usage: %prog configure"
     , version=_VERSION)
    options, args = parser.parse_args(args)
    
    cfg = MainConfig(os.getcwd(), failinpc=True)
    man = pmodules.ModuleManager(cfg.fullSource())
    man.initModules(cfg.targets)
    path = os.path.join(cfg.config_dir, _PC_CCF)
    config = dict()
    if os.path.isfile(path):
        config = pfile.loadConfigFile(path)
    man.loadNodes(config=config)
    ctrl = cfgcontrol.ConfigController(Pbgui, man)
    save_settings = ctrl.mainloop()
    if save_settings:
        print("Is fully configured: "
             , man.isFullyConfigured(warning=True))
        pfile.saveConfigFile(path, man.collectConfig())


def make(args):
    parser = OptionParser(usage="usage: %prog make [options]"
     , version=_VERSION)
    parser.add_option("-n", "--not-interactive", dest="interactive"
     , help="Use this flag to disable interactive mode."
     , default=True, action="store_false")
    parser.add_option("-l", "--load-config", dest="load"
    , help="Load a config file before starting build process")
    options, args = parser.parse_args(args)
    
    cfg = MainConfig(os.getcwd(), failinpc=True)
    
    if options.load is None:
        path = os.path.join(cfg.config_dir, _PC_CCF)
    else:
        path = options.load
    
    config = pfile.loadConfigFile(path)
    man = pmodules.ModuleManager(cfg.fullSource())
    man.initModules(cfg.targets)
    man.loadNodes(config=config)
    
    if options.interactive:
        while not man.isFullyConfigured():
            ctrl = cfgcontrol.ConfigController(Pbgui, man)
            if not ctrl.mainloop():
                print("exiting")
                return
    if not man.isFullyConfigured():
        return
    output = man.collectConfig(formatted=True)
    for name, mod in output.items():
        print("%s:" % name)
        for key, value in mod.items():
            print(" - %s = '%s'" % (key, str(value)))
    man.generateOutput(cfg.fullDestination())


def showMain(args, cmd):
    parser = OptionParser(usage=_CMD_USAGE
     , description=_CMD_DESC, version=_VERSION)
    options, args = parser.parse_args(args)
    
    if cmd is not None:
        print("invalid command '%s'" % cmd)


def main(args):
    
    cmd = None
    try:
        cmd = args[1]
        if cmd in ('setup', 'init', 'su'):
            return setup(args[2:])
        elif cmd == 'add':
            return add(args[2:])
        elif cmd in ('rm', 'remove'):
            return rm(args[2:])
        elif cmd in ('status', 'st'):
            return status(args[2:])
        elif cmd == 'make':
            return make(args[2:])
        elif cmd in ('cfg', 'config', 'configure'):
            return configure(args[2:])
    except IndexError:
        pass
    except SourceNotFoundError as e:
        print("Couldn't find source directory (%s)" % e.path)
    except NotProperlyConfiguredError as e:
        print("Not properly configured.\n%s" % e.error_source)
        print("Use 'setup' command to set up project.")
    
    return showMain(args, cmd)


if __name__ == '__main__':
    main(sys.argv)
