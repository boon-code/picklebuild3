#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module is about loading and saving files.

This module covers loading and saving external files:

- loading configuartion files
- loading main config file
"""

import json


__author__ = 'Manuel Huber'
__copyright__ = "Copyright (c) 2011 Manuel Huber."
__license__ = 'GPLv3'
__docformat__ = "restructuredtext en"


def loadConfigFile(path):
    
    with open(path, "r") as f:
        return json.load(f)

def saveConfigFile(path, objs):
    
    with open(path, "w") as f:
        json.dump(objs, f)

loadControlFile = loadConfigFile
saveControlFile = saveConfigFile
