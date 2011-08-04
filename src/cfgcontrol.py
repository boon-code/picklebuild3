# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

from warnings import warn
import collections

from pexcept import NotYetWorkingWarning
import pmodules
import pfile

"""
Controller part of MVC pattern.
"""

__author__ = 'Manuel Huber'
__license__ = 'GPLv3'

class ConfigController(object):
    
    def __init__(self, gui_class, mod_man):
        self._mman = mod_man
        self._gui = gui_class(self)
        names = mod_man.getModuleNames()
        self._gui.initModules(names)
        self._cur_mod = None
        self._cur_node = None
        self._cur_value = None
        self._gui.mainloop()
    
    # called by gui:
    
    def loadConfig(self, path):
        self._cur_mod = None
        self._cur_node = None
        self._cur_value = None
        names = self._mman.getModuleNames()
        self._gui.initModules(names)
        config = pfile.loadConfigFile(path)
        self._mman.loadNodes(config=config)
    
    def saveConfig(self, path):
        config = self._mman.collectConfig()
        pfile.saveConfigFile(path, config)
    
    def finish(self):
        
        #self.applyChoice()
        
        #TODO: delete!
        self._mman.dump()
        
        return True
    
    def cancel(self):
        
        #TODO: delete!
        self._mman.dump()
        pass
    
    def iterColors(self, names):
        for name in names:
            node = self._cur_mod.getNode(name, False)
            if node.isDisabled():
                yield 'grey'
            else:
                if node.isConfigured():
                    yield 'green'
                else:
                    yield 'black'
    
    def chooseModule(self, name):
        #self.applyChoice()
        mod = self._mman.getModule(name)
        if self._cur_mod is mod:
            return True
        else:
            self._cur_node = None
            self._cur_mod = mod
            self._gui.setModuleHelp(mod.dumpsInfo())
            names = mod.getNodeNames()
            colors = tuple(self.iterColors(names))
            self._gui.initNodes(names, colors)
            self._do_update()
    
    def chooseNode(self, name):
        #self.applyChoice()
        node = self._cur_mod.getNode(name)
        if self._cur_node is not None:
            if self._cur_node.getName() == name:
                self._cur_node = node
                self._gui.setNodeHelp(node.help)
                return True
        self._cur_node = node
        self._gui.setNodeHelp(node.help)
        return self.loadChoice()
    
    def applyChoice(self):
        
        ret = self._real_apply()
        self._do_update()
        return ret
    
    def _do_update(self):
        
        if self._cur_mod is not None:
            self._cur_mod.executeFrames()
            names = self._cur_mod.getNodeNames()
            if self._cur_node is not None:
                name = self._cur_node.getName()
                self._cur_node = None
                for (i, v) in enumerate(names):
                    if v == name:
                        default_index = i
                        self._cur_node = self._cur_mod.getNode(v, False)
            colors = tuple(self.iterColors(names))
            print("bad _do_update")
            self._gui.updateNodes(names, colors)
    
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
        
        print("APPLY NOT DONE.")
        return False
    
    def loadChoice(self):
        self._cur_value = None
        if None not in (self._cur_node, self._cur_mod):
            node = self._cur_node
            nt = node.getNodeType()
            value = None
            if node.isDisabled():
                print("print disabled")
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
            self.applyChoice()
