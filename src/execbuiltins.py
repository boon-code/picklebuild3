__builtins__ = dict()

def open(*args, **kargs):
    raise Exception("Not allowed")

def getattr(attr_name):
    blacklist = ('__debug__', '__import__', 'eval', 'exec'
     , 'open', 'compile')
    if attr_name in blacklist:
        raise Exception("Not allowed")
    else:
        import builtins
        return builtins.getattr(attr_name)

