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
        super(PickleBuildException, self).__init__(*args)


class BasicXmlException(PickleBuildException):
    
    def __init__(self, *args):
        super(BasicXmlException, self).__init__(*args)


class XmlMissingAttributesError(BasicXmlException):
    
    def __init__(self, *args):
        super(XmlMissingAttributesError, self).__init__(*args)
        self.attribute_list = []


class NotYetWorkingWarning(UserWarning):
    pass
