#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Manuel Huber'
__copyright__ = "Copyright (c) 2011 Manuel Huber."
__license__ = 'GPLv3'
__docformat__ = "restructuredtext en"


class PickleBuildException(Exception):
    """Basic picklebuild exception.
    
    Should be used as base class for every new Exception picklebuild
    raises.
    """
    
    def __init__(self, *args):
        """Basic picklebuild exception constructor.
        
        :param args: These parameter will be passed
                     to the Exception class.
        """
        Exception.__init__(*args)


class NotYetWorkingWarning(UserWarning):
    pass


class HiddenObject(object):
    """This is a base class for classes with hidden members.
    
    Subclasses of this class will hide it's members except 
    a given subset.
    """
    
    def __init__(self, objects):
        """This initializes a new instances.
        
        :param objects: A dict that contains all members that
                        shall be accessable.
        """
        self._objs = objects
    
    def __getattribute__(self, attr_name):
        """Reimplemented getattribute mechanism to hide members.
        
        :param attr_name: name of element that shall be accessed.
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
        """Reimplement *dir* method to hide members.
        
        Only certain members (in *self._objs* dict) will be shown.
        """
        objs = object.__getattribute__(self, '_objs')
        return list(objs.keys())

