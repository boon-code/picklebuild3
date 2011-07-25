class HiddenObject(object):
    
    def __init__(self, objects):
        self._objs = objects
    
    def __getattribute__(self, attr_name):
        objs = object.__getattribute__(self, '_objs')
        if attr_name in objs:
            return objs[attr_name]
        else:
            class_ = object.__getattribute__(self, '__class__')
            raise AttributeError(
                "'%s' doesn't have an attribute named '%s'"
                % (str(class_.__name__), attr_name))
    
    def __dir__(self):
        objs = object.__getattribute__(self, '_objs')
        return list(objs.keys())


class Node(HiddenObject):
    
    def __init__(self, name):
        d = {'name' : name}
        HiddenObject.__init__(self, d)


class ExternalNode(HiddenObject):
    
    def __init__(self, mod_name, name):
        
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

