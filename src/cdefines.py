#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This module covers C-Header file generation.

This will be used by pconfig to extend the **make** command
to generate C-Header files that define all variables.
"""

from warnings import warn
from os.path import join


__author__ = 'Manuel Huber'
__copyright__ = "Copyright (c) 2011 Manuel Huber."
__license__ = 'GPLv3'
__docformat__ = "restructuredtext en"

_HEADER_FILE = 'configure_%s.h'
_DEFINE_LINE = '#define %s (%s)\n'


def generateHeader(mod, dst, cfgdict):
    """This method generates the C-Header file.
    
    :param mod:     The module which will be processed.
    :param dst:     Destination path of the output directory.
    :param cfgdict: A dictionary that contains all variables
                    that should be added to the C-Header file.
    """
    modpath = join(dst, mod.relativepath())
    path = join(modpath, _HEADER_FILE % mod.uniquename())
    
    with open(path, 'w') as f:
        for key, value in cfgdict.items():
            f.write(_DEFINE_LINE % (key, str(value)))

