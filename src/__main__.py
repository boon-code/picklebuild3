#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""This is the start script of this program

If all files get zipped, they can be directly executed 
with a little start script (I did not *invent* this...).
"""

import sys
import logging
from pconfig import main


__author__ = 'Manuel Huber'
__copyright__ = "Copyright (c) 2011 Manuel Huber."
__license__ = 'GPLv3'
__docformat__ = "restructuredtext en"


main(sys.argv, logging.ERROR)
