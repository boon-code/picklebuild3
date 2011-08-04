# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

from warnings import warn
import os.path


"""
This module implements basic classes to handle target-files.
"""

__author__ = 'Manuel Huber'
__license__ = 'GPLv3'


class SkippedTargetWarning(UserWarning):
    """Warns about invalid file-paths.
    
    Invalid file-paths are for example:
     - Files that don't share the same root directory (the source
       directory).
     - Paths that are no regular files.
    """
    pass

class Target(object):
    """This class represents a single target file
    
    Used to implement additional arguments.
    """
    
    def __init__(self, name, options):
        """Initializes a new instance.
        
        @param name:    file-name.
        @param options: Addtitional options regarding this file.
        """
        self.name = name
        self.options = options
    
    def __str__(self):
        return self.name


class TargetNode(object):
    """This class represents one target directory.
    
    This node will only contain files that belong to the same
    directory.
    """
    
    def __init__(self, module_path):
        """Initializes a new instance.
        
        This TargetNode will be indentified by it's module path
        (relative to the src directory)
        @param module_path: path to this directory (including this
                            directory name.)
        """
        self._path = module_path
        self._targets = dict()
            
    def add(self, filename, **options):
        """Adds a file to this node.
        
        This method adds a new file to this TargetNode.
        @param filename: File name which will be added.
        @param options:  
        """
        self._targets[filename] = Target(filename, options)
    
    def remove(self, filename):
        """Removes a file from this node.
        
        If the file doesn't exist, it will just be ignored.
        @param filename: File to remove.
        @returns:        Number of nodes that remain.
        """
        if self._targets.pop(filename, None) is None:
            warn("Couldn't find target '%s'" % filename
                 , SkippedTargetWarning)
        return len(self._targets)
    
    def modulepath(self, src=None):
        """This method can be used to retrieve the module path.
        
        @param src: src will be appended to the module path.
        @returns: The module path.
        """
        if not (src is None):
            path = os.path.join(src, self._path)
            return os.path.normpath(path)
        else:
            return self._path
    
    def iterNames(self, src=None):
        """This generator should be used to get all filenames.
        
        @param src: The source directory name that will be appended to
                    the path and name. 
                    (None means don't append anything)
        """
        path = self.modulepath(src=src)
        for name in self._targets.keys():
            filepath = os.path.join(path, name)
            yield os.path.normpath(filepath)
    
    def items(self, src=None):
        """This generator returns all nodes.
        
        @param src: The source directory that will be appended.
        """
        path = self.modulepath(src=src)
        for (n, v) in self._targets.items():
            filepath = os.path.normpath(os.path.join(path, n))
            yield (filepath, v)


class TargetTree(object):
    """This class represents a list of target directories.
    
    The target directories (class: TargetNode) contains all files
    in that directory that have to be processed.
    If you iterate through all of them, you get the target-tree.
    """
    
    def __init__(self, rootdir):
        """Initializes a new instance.
        
        @param rootdir: Root directory of this tree.
        """
        self._src = rootdir
        self._nodes = dict()
    
    def add(self, filepath, relative=False, **options):
        """Adds a new path to this object.
        
        @param filepath: The path to add.
        @param relative: Optional parameter; if set, filepath will be
                         interpreted as relative path, not absolute
                         (or relative to cwd).
        """
        if relative:
            rpath = filepath
        else:
            rpath = os.path.relpath(filepath, self._src)
        
        fullpath = os.path.normpath(os.path.join(self._src, rpath))
        
        if not (fullpath.startswith(self._src)):
            warn("Invalid target '%s' skipped."
                 % fullpath, SkippedTargetWarning)
            return False
        
        if os.path.isfile(fullpath):
            split_path = os.path.split(rpath)
            mdir = os.path.normpath(split_path[0])
            if mdir not in self._nodes:
                self._nodes[mdir] = TargetNode(mdir)
            self._nodes[mdir].add(split_path[1], **options)
            return True
        else:
            warn("Invalid target (not a file) '%s' skipped."
                % fullpath, SkippedTargetWarning)
            return False
    
    def remove(self, filepath, relative=False):
        """Deletes a file from this tree.
        
        @param filepath: Path to file that should be removed.
        @param relative: filepath will be interpreted as relative
                         path (if relative == True). If not set,
                         filepath will be interpreted either as 
                         absolute path, or relative to the current
                         working directory (cwd).
        """
        if relative:
            rpath = filepath
        else:
            rpath = os.path.relpath(filepath, self._src)
        
        splitpath = os.path.split(rpath)
        rdir = os.path.normpath(splitpath[0])
        node = self._nodes.pop(rdir, None)
        if node is not None:
            if node.remove(splitpath[1]) > 0:
                self._nodes[rdir] = node
        else:
            warn("TargetNode '%s' not found, skipping"
                 % rdir, SkippedTargetWarning)
    
    def iterNames(self, relative=True):
        
        for (path, node) in self._nodes.items():
            if relative:
                for i in node.iterNames():
                    yield i
            else:
                for i in node.iterNames(src=self._src):
                    yield i
    
    def getTargetNode(self, relpath):
        
        if relpath in self._nodes:
            return self._nodes[relpath]
    
    def iterDirs(self):
        return self._nodes.values()
    
    def dumpTree(self):
        
        for (k,v) in self._nodes.items():
            print("'%s':" % k)
            for file in v.iterNames():
                print("  - '%s'" % file)
    
    
        
