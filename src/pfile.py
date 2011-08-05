#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

"""
This module covers loading and saving external files:
    - loading configuartion files
    - loading main config file
"""

__author__ = 'Manuel Huber'
__license__ = 'GPLv3'

def loadConfigFile(path):
    
    with open(path, "r") as f:
        return json.load(f)

def saveConfigFile(path, objs):
    
    with open(path, "w") as f:
        json.dump(objs, f)

loadControlFile = loadConfigFile
saveControlFile = saveConfigFile
