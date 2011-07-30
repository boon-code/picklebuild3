import os.path
import warnings


"""
Copyright (c) 2011 Manuel Huber.
License: GPLv3.
"""

__author__ = 'Manuel Huber'
__license__ = 'GPLv3'


class SkippedTargetWarning(UserWarning):
    """Warns about invalid file-paths.
    
    Invalid file-paths are for example:
     * Files that don't share the same root directory (the source
       directory).
     * Paths that are no regular files.
    """
    pass


class TargetNode(object):
    
    def __init__(self, module_path):
        """
        This TargetNode will be indentified by it's module path
        (relative to the src directory)
        @param module_path: path to this directory (including this
                            directory name.)
        """
        self._path = module_path
        self._target_names = []
            
    def add(self, filename):
        """
        This method adds a new file to this TargetNode.
        @param filename: File name which will be added.
        """
        self._target_names.append(filename)
    
    def modulepath(self, src=None):
        """
        This method can be used to retrieve the module path.
        @param src: src will be appended to the module path.
        @returns: The module path.
        """
        if not (src is None):
            path = os.path.join(src, self._path)
            return os.path.normpath(path)
        else:
            return self._path
    
    def iterFiles(self, src=None):
        """
        This generator should be used to get all filenames.
        
        @param src: The source directory name that will be appended to
                    the path and name. 
                    (None means don't append anything)
        """
        path = self.modulepath(src=src)
        for name in self._target_names:
            filepath = os.path.join(path, name)
            yield os.path.normpath(filepath)


class TargetList(object):
    
    def __init__(self, source_dir):
        
        self._src = source_dir
        self._nodes = {}
    
    def add(self, filepath):
        """
        Adds a new path to this object.
        Only relative paths relative to src
        will be accepted.
        
        param filepath: The path to add (relative to src).
        """
        rpath = os.path.normpath(os.path.join(self._src, filepath))
        
        if not (rpath.startswith(self._src)):
            warnings.warn("Invalid target '%s' skipped."
                 % filepath, SkippedTargetWarning)
            return False
        
        if os.path.isfile(rpath):
            split_path = os.path.split(filepath)
            mdir = os.path.normpath(split_path[0])
            if mdir not in self._nodes:
                self._nodes[mdir] = TargetNode(mdir)
            self._nodes[mdir].add(split_path[1])
            return True
        else:
            warnings.warn("Invalid target (not a file) '%s' skipped."
                % filepath, SkippedTargetWarning)
            return False
    
    def getTargetNode(self, relpath):
        
        if relpath in self._nodes:
            return self._nodes[relpath]
    
    def iterDirs(self):
        
        for key in self._nodes:
            yield self._nodes[key]
    
    def dumpTree(self):
        
        for (k,v) in self._nodes.items():
            print("'%s':" % k)
            for file in v.iterFiles():
                print("  - '%s'" % file)
    
    
        
