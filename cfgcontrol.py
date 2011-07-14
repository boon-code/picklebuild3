from warnings import warn
import collections

from pexcept import NotYetWorkingWarning
import pmodules

class DummyOption(object):
    
    @classmethod
    def is_list_instance(cls, list):
        
        if isinstance(list, str):
            return False
        else:
            return isinstance(list, collections.Sequence)
    
    def __init__(self, lst=None, choice=None, multi=False
        , disabled=False, available=True):
        
        is_choice_list = DummyOption.is_list_instance(choice)
        if DummyOption.is_list_instance(lst):
            if is_choice_list:
                multi = True
            
            if multi:
                self._type = pmodules.CT_MULTI
            else:
                self._type = pmodules.CT_LIST
        else:
            self._type = pmodules.CT_TEXT
            if is_choice_list:
                choice = None
        
        self._list = lst
        self._choice = choice
        self._disabled = disabled
        self._available = available
        
        if choice is None:
            self._configured = False
        else:
            self._configured = True
    
    def getNodeType(self):
        return self._type
    
    def isConfigured(self):
        return self._configured
    
    def isAvailable(self):
        return self._available
    
    def isDisabled(self):
        return self._disabled
    
    def get_choice(self):
        return self._choice
    
    def set_choice(self, choice):
        self._choice = choice
        return True
    
    def get_list(self):
        return self._list
    
    def _set_name(self, name):
        self._name = name
    
    def getName(self):
        return self._name


class DummyModMan(object):
    
    def __init__(self):
        
        self._mods = {}
        mod1 = {'MUESLI' : DummyOption(lst=["Fruit Loops", "Clusters", "Vital"], choice="Clusters")
            , 'KAFFEE' : DummyOption(lst=["Ja", "Nein"], disabled=True)
            , 'TEE' : DummyOption(lst=["Ja", "Nein"], available=False)
            , 'VERFEINERUNG' : DummyOption(lst=["Milch", "Zucker"], choice=["Milch", "Zucker", "Honig"], multi=True)
            }
        self._mods['BREAKFAST'] = mod1
        mod2 = {'BLA' : DummyOption(choice="Some Text")
            , 'SPRACHEN' : DummyOption(lst=("Finisch", "Deutsch", "Englisch"), choice=["Finisch", "Deutsch"])
            }
        self._mods['BLA'] = mod2
        
        for mod_name in self._mods:
            for opt_name in self._mods[mod_name]:
                self._mods[mod_name][opt_name]._set_name(opt_name)
    
    def get_module_list(self):
        return list(self._mods.keys())
    
    def get_node_list(self, mod_name):
        return list(self._mods[mod_name].values())
    
    def get_node(self, mod_name, node_name):
        return self._mods[mod_name][node_name]
    
    def dump(self):
        """
        Shows module config.
        """
        for (mod_name, mod) in self._mods.items():
            print("%s:" % mod_name)
            for (opt_name, option) in mod.items():
                choice = option.get_choice()
                if choice is None:
                    choice = "<Was None>"
                else:
                    if option.getNodeType() == pmodules.CT_MULTI:
                        choice = str(tuple(i for i in choice))
                print("  - %s: %s" % (opt_name, choice))


class ConfigController(object):
    
    _TEXT = 'text'
    _LIST = 'list'
    _MULTI = 'multi'
    
    def __init__(self, gui_class, mod_man):
        self._mman = mod_man
        self._gui = gui_class(self)
        self._gui.initModules(mod_man.get_module_list())
        self._cur_mod = None
        self._cur_node = None
        self._opt_type = None
        self._cur_opt = None
        self._gui.mainloop()
    
    # called by gui:
    
    def loadConfig(self, filename):
        pass
    
    def saveConfig(self, filename):
        pass
    
    def finish(self):
        
        self.applyChoice()
        
        #TODO: delete!
        self._mman.dump()
        
        return True
    
    def cancel(self):
        
        #TODO: delete!
        self._mman.dump()
        pass
    
    def chooseModule(self, name):
        self.applyChoice()
        if self._cur_mod == name:
            return True
        else:
            self._cur_node = None
            self._cur_opt = None
            self._opt_type = None
            self._cur_mod = name
            self._gui.initNodes(self._mman.get_node_list(name))
            return True
    
    def chooseNode(self, name):
        self.applyChoice()
        if self._cur_node == name:
            return True
        else:
            self._cur_node = name
            return self.reloadChoice()
    
    def applyChoice(self):
        values = (self._cur_mod, self._cur_node, self._cur_opt
                 , self._opt_type)
        if None not in values:
            node = self._mman.get_node(self._cur_mod, self._cur_node)
            if self._opt_type == ConfigController._TEXT:
                return node.set_choice(self._cur_opt)
            elif self._opt_type == ConfigController._LIST:
                return node.set_choice(self._cur_opt[0])
            elif self._opt_type == ConfigController._MULTI:
                return node.set_choice(self._cur_opt)
        return False
    
    def reloadChoice(self):
        if None not in (self._cur_mod, self._cur_node):
            node = self._mman.get_node(self._cur_mod, self._cur_node)
            self._cur_opt = None
            node_type = node.getNodeType()
            if node_type == pmodules.CT_TEXT:
                self._opt_type = ConfigController._TEXT
                self._gui.setTextNode(node.get_choice())
            elif node_type == pmodules.CT_LIST:
                self._opt_type = ConfigController._LIST
                self._gui.setListNode(node.get_list(), node.get_choice())
            elif node_type == pmodules.CT_MULTI:
                self._opt_type = ConfigController._MULTI
                self._gui.setMultiNode(node.get_list(), node.get_choice())
            else:
                return False
            return True
        else:
            return False
    
    def setChoice(self, choice):
        values = (self._cur_mod, self._cur_node, self._opt_type)
        if None not in values:
            self._cur_opt = choice

from pbgui_imp import Pbgui
man = DummyModMan()
ctrl = ConfigController(Pbgui, man)
