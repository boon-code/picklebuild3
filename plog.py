

"""
This module is about logging. It should be extented by
new create_xxx_logger functions. If you want to be able to
easily change the way logging will be done, use the 
clone_system_logger method, which will use the globally configured
(using setMethod) method to create new logger.

Don't directly modify variables starting with the '_' 
character. This module will be thread-safe as long as
you only use the create_xxx_logger methods in
setMethods().
"""

import sys
import logging
import threading

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

# it has to be an RLock (see clone_system_logger for example)
_lock = threading.RLock()

_level = DEBUG
_format_string = ("%(name)s : %(threadName)s "
    + ": %(levelname)s : %(message)s")

_clone_system_logger = None

def setLevel(level):
    """
    This method set the system level.
    
    @param level:   This is the new system log level.
                    This value will be used on creation
                    of new logger objects.
    """
    global _level
    
    _lock.acquire()
    try:
        _level = level
    finally:
        _lock.release()


def setMethod(method):
    """
    Defines, which method should be used to create
    new logger objects.
    
    @param method:  The new default method (used by
                    clone_system_logger). This should
                    be a method of plog.
    """
    global _clone_system_logger
    
    _lock.acquire()
    try:
        _clone_system_logger = method
    finally:
        _lock.release()


def create_stderr_logger(name):
    """
    Creates a standard logger (to stderr)
    
    This method is intent thread safe. There shouldn't be
    any problems.
    
    @param name:    This is the name for the logger object.
    @return:        The actual logging object that can be used 
                    to really log messages to the screen.
    """
    
    _lock.acquire()
    try:
        log = logging.getLogger(name)
        log.setLevel(_level)
        if len(log.handlers) <= 0:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(_format_string))
            log.addHandler(handler)
        
        return log
    finally:
        _lock.release()

def clone_system_logger(name):
    """
    Creates a new logger object, using the current
    system (plog) settings.
    
    If you pass a wrong method to setMethod, there could
    very likly be a TypeError Exception.
    
    @param name: The name of the new logger object.
    @type name:  string
    @return:     The new logger object.
    @rtype:      logging.Logger
    """
    
    _lock.acquire()
    try:
        if _clone_system_logger is None:
            return create_stderr_logger(name)
        else:
            return _clone_system_logger(name)
    finally:
        _lock.release()
    
