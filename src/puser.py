# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

"""
This file contains objects that are used by the external script
file. Only these objects can directly be modified by the
script.
An instance of ScriptObject has to be used by the script to create
nodes. To reference these nodes, ScriptObject returns instances of
Node. These objects only contain the name of the node.
External Nodes can only be used through an ExternalScriptObject
which can be accessed by using extension commands. Since external
references have to be resolved stepwise after they have been set up,
one can simply access external nodes just like it was a member of
ExternalScriptObject. These references will be resolved afterwards
and if not possible, an error should occur.

TODO: Some parts of the text above haven't been implemented yet. 
Especially resolving doesn't work stepwise yet.
"""

__author__ = 'Manuel Huber'
__license__ = 'GPLv3'

class HiddenObject(object):
    """This is a base class for classes with hidden members.
    
    Subclasses of this class will hide it's members except 
    a given subset.
    """
    
    def __init__(self, objects):
        """This initializes a new instances.
        
        @param objects: A dict that contains all members that
                        shall be accessable.
        """
        self._objs = objects
    
    def __getattribute__(self, attr_name):
        """Reimplemented getattribute mechanism to hide members.
        
        @param attr_name: name of element that shall be accessed.
        """
        objs = object.__getattribute__(self, '_objs')
        if attr_name in objs:
            return objs[attr_name]
        else:
            class_ = object.__getattribute__(self, '__class__')
            raise AttributeError(
                "'%s' doesn't have an attribute named '%s'"
                % (str(class_.__name__), attr_name))
    
    def __dir__(self):
        """Reimplement __dir__ method to hide members.
        
        Only certain members (in _objs dict) will be shown.
        """
        objs = object.__getattribute__(self, '_objs')
        return list(objs.keys())


class Node(HiddenObject):
    """This class is used to reference nodes.
    
    This object will just contain the name of the node that it
    references.
    """
    
    def __init__(self, name):
        """Initializes a new instance.
        
        @param name: Name of this node.
        """
        d = {'name' : name}
        HiddenObject.__init__(self, d)


class ExternalNode(HiddenObject):
    """This class is used to reference external nodes.
    
    External nodes are nodes from 'used' modules (extension).
    This is not the same as 'Node', since these objects don't 
    actual reference a certain object. External nodes have to be
    matched to existing nodes as soon as the referenced module
    will be configured.
    """
    
    def __init__(self, mod_name, name):
        """Initializes a new instances.
        
        @param mod_name: Name of the external module that this node
                         references to.
        @param name:     Name of the node.
        """
        d = {'name' : name, 'module' : mod_name}
        HiddenObject.__init__(self, d)


class ExternalScriptObject(object):
    
    def __init__(self, mod_name, node_dict):
        """Creates a new instance.
        
        @param mod_name:  Name of this module.
        @param node_dict: This dict instance will be filled with
                          all nodes that have been created.
        """
        self._mod = mod_name
        self._nodes = node_dict
    
    def __getattribute__(self, attr_name):
        
        nodes = object.__getattribute__(self, '_nodes')
        if attr_name == '__getitem__':
            return object.__getattribute__(self, '__getitem__')
        elif attr_name == '__contains__':
            return object.__getattribute__(self, '__contains__')
        elif attr_name not in nodes:
            mod_name = object.__getattribute__(self, '_mod')
            nodes[attr_name] = ExternalNode(mod_name, attr_name)
        return nodes[attr_name]
    
    def __dir__(self):
        # just for debugging
        nodes = object.__getattribute__(self, '_nodes')
        return list(nodes.keys())
    
    def __getitem__(self, name):
        # just for debugging
        nodes = object.__getattribute__(self, '_nodes')
        if name in nodes:
            return nodes[name]
        else:
            raise KeyError("No item with name '%s'" % name)
    
    def __contains__(self, name):
        # just for debugging
        nodes = object.__getattribute__(self, '_nodes')
        return (name in nodes)


class ScriptObject(object):
    
    def __init__(self, mod):
        self._mod = mod
        self._names = ('string', 'expr', 'single', 'multi', 'depends'
             , 'override', 'define')
    
    def __getattribute__(self, name):
        names = object.__getattribute__(self, '_names')
        if name in names:
            return object.__getattribute__(self, name)
        else:
            raise AttributeError("ScriptObject doesn't have an "
                + "attribute named '%s'" % name)
    
    def __dir__(self):
        names = object.__getattribute__(self, '_names')
        return list(names)
    
    def define(self, name, value, **options):
        mod = object.__getattribute__(self, '_mod')
        return mod.define(name, value, options)
    
    def string(self, name, **options):
        mod = object.__getattribute__(self, '_mod')
        return mod.string(name, options)
    
    def expr(self, name, **options):
        mod = object.__getattribute__(self, '_mod')
        return mod.expr(name, options)
    
    def single(self, name, darray, **options):
        mod = object.__getattribute__(self, '_mod')
        return mod.single(name, darray, options)
    
    def multi(self, name, darray, **options):
        mod = object.__getattribute__(self, '_mod')
        return mod.multi(name, darray, options)
    
    def depends(self, *deps):
        mod = object.__getattribute__(self, '_mod')
        return mod.depends(deps)
    
    def override(self, ext, node, **options):
        mod = object.__getattribute__(self, '_mod')
        return mod.override(ext, node, options)

