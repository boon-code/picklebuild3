from warnings import warn
import collections

from pexcept import NotYetWorkingWarning
import pmodules


class ConfigController(object):
    
    def __init__(self, gui_class, mod_man):
        self._mman = mod_man
        self._gui = gui_class(self)
        self._gui.initModules(mod_man.getModuleNames())
        self._cur_mod = None
        self._cur_node = None
        self._cur_value = None
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
        mod = self._mman.getModule(name)
        
        if self._cur_mod is mod:
            return True
        elif mod is None:
            return False
        else:
            self._cur_node = None
            self._cur_mod = mod
            names = mod.getNodeNames()
            self._gui.initNodes(names)
    
    def chooseNode(self, name):
        self.applyChoice()
        node = self._cur_mod.getNode(name)
        if self._cur_node is node:
            return True
        else:
            self._cur_node = node
            return self.loadChoice()
    
    def applyChoice(self):
        ret = self._real_apply()
        # TODO: update!
        print("do update")
        return ret
    
    def _real_apply(self):
        if None not in (self._cur_mod, self._cur_node, self._cur_value):
            node = self._cur_node
            if node.isDisabled():
                return False
            
            nt = node.getNodeType()
            if nt == pmodules.NT_TEXT:
                return node.setValue(self._cur_value)
            elif nt == pmodules.NT_LIST:
                value = tuple(self._cur_value)
                if len(value) != 1:
                    return False
                return node.chooseByIndex(value[0])
            elif nt == pmodules.NT_MULTI:
                return node.chooseIndices(self._cur_value)
            else:
                return True
        return False
    
    def loadChoice(self):
        self._cur_value = None
        if None not in (self._cur_node, self._cur_mod):
            node = self._cur_node
            nt = node.getNodeType()
            value = None
            if node.isDisabled():
                self._gui.setConstNode("<<disabled>>")
            else:
                if nt == pmodules.NT_CONST:
                    if node.isConfigured():
                        value = node.readValue()
                    self._gui.setConstNode(value)
                elif nt == pmodules.NT_TEXT:
                    if node.isConfigured():
                        value = node.readValue()
                    self._gui.setTextNode(value)
                elif nt == pmodules.NT_LIST:
                    if node.isConfigured():
                        value = node.getIndex()
                    self._gui.setListNode(node.getViewList(), value)
                elif nt == pmodules.NT_MULTI:
                    if node.isConfigured():
                        value = node.getIndices()
                    self._gui.setMultiNode(node.getViewList(), value)
                else:
                    return False
                return True
        else:
            return False
    
    def setChoice(self, choice):
        if None not in (self._cur_mod, self._cur_node):
            self._cur_value = choice
