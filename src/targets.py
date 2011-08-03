# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

import os.path
import warnings


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
        self._target_names = []
            
    def add(self, filename):
        """Adds a file to this node.
        
        This method adds a new file to this TargetNode.
        @param filename: File name which will be added.
        """
        self._target_names.append(filename)
    
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
    
    def iterFiles(self, src=None):
        """This generator should be used to get all filenames.
        
        @param src: The source directory name that will be appended to
                    the path and name. 
                    (None means don't append anything)
        """
        path = self.modulepath(src=src)
        for name in self._target_names:
            filepath = os.path.join(path, name)
            yield os.path.normpath(filepath)


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
    
    def add(self, filepath):
        """Adds a new path to this object.
        
        param filepath: The path to add.
        """
        rpath = os.path.relpath(filepath, self._src)
        fullpath = os.path.normpath(os.path.join(self._src, rpath))
        
        if not (fullpath.startswith(self._src)):
            warnings.warn("Invalid target '%s' skipped."
                 % filepath, SkippedTargetWarning)
            return False
        
        if os.path.isfile(fullpath):
            split_path = os.path.split(rpath)
            mdir = os.path.normpath(split_path[0])
            if mdir not in self._nodes:
                self._nodes[mdir] = TargetNode(mdir)
            self._nodes[mdir].add(split_path[1])
            return True
        else:
            warnings.warn("Invalid target (not a file) '%s' skipped."
                % filepath, SkippedTargetWarning)
            return False
    
    def remove(self, filepath):
        rpath = os.path.relpath(filepath, self._src)
        rdir = os.path.normpath(os.path.split(rpath)[0])
        self._nodes.pop(rdir, None)
        # TODO: this is wrong, only delete entry in TreeNode...
    
    def getTargetNode(self, relpath):
        
        if relpath in self._nodes:
            return self._nodes[relpath]
    
    def iterDirs(self):
        return self._nodes.values()
    
    def dumpTree(self):
        
        for (k,v) in self._nodes.items():
            print("'%s':" % k)
            for file in v.iterFiles():
                print("  - '%s'" % file)
    
    
        
