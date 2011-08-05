#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2011 Manuel Huber.
# License: GPLv3.

from pbgui import CustomPbgui
import sys

if sys.version_info[0] == 3:
    import tkinter
    from tkinter.filedialog import *
elif sys.version_info[0] == 2:
    import Tkinter
    from tkFileDialog import *

"""
Implements methods for pbgui.CustomPbgui.
"""

__author__ = 'Manuel Huber'
__copyright__ = "Copyright (c) 2011 Manuel Huber."
__license__ = 'GPLv3'
__docformat__ = "restructuredtext en"

class Pbgui(CustomPbgui):
    
    def __init__(self, controller):
        root = tkinter.Tk()
        CustomPbgui.__init__(self, root)
        self._root = root
        self._ctrl = controller
        root.bind("<<ListboxSelect>>", self._listbox_event_handler)
        root.bind("<KeyRelease>", self._testbox_event_handler)
        self._sclModules["command"] = self._lsModules.yview
        self._sclNodes["command"] = self._lsNodes.yview
        self._sclListconfig["command"] = self._lsListconfig.yview
        self._sclTextconfig["command"] = self._txTextconfig.yview
        self._labModules.config(text="                          ")
        self._labNodes.config(text="                          ")
        self._labConfig.config(text="                          ")
        root.protocol("WM_DELETE_WINDOW", root.destroy)
    
    # override
    def _butCancel_command(self, *args):
        self._ctrl.cancel()
        self._root.destroy()
    
    #override
    def _butOk_command(self, *args):
        if self._ctrl.finish():
            self._root.destroy()
    
    #override
    def _butLoadfile_command(self, *args):
        path = askopenfilename(filetypes = [('config', '*.jso')]
             , title = "open file")
        
        if path != '':
            self._ctrl.loadConfig(path)
    
    #override
    def _butSavefile_command(self, *args):
        path = asksaveasfilename(filetypes = [('config', '*.jso')]
             ,title = "save file")
        
        if path != '':
            self._ctrl.saveConfig(path)
    
    #override
    def _butReset_command(self, *args):
        self._ctrl.reloadChoice()
    
    #override
    def _butApply_command(self, *args):
        #print("apply: ", self._ctrl.applyChoice())
        pass
    
    def _lsNodes_selected(self, node_name):
        self._ctrl.chooseNode(node_name)
    
    def _lsModules_selected(self, mod_name):
        self._ctrl.chooseModule(mod_name)
    
    def _lsListconfig_selected(self, choice):
        self._ctrl.setChoice(choice)
    
    def _int_list(self, str_list):
        return tuple((int(i) for i in str_list))
    
    def _listbox_event_handler(self, event):
        """Will be called by the <<ListboxSelect>> virtual event.
        
        :param event: Additional event arguments (Not used).
        """
        cur_module = self._lsModules.curselection()
        if len(cur_module) != 1:
            cur_module = None
        else:
            cur_module = self._lsModules.get(cur_module)
            
        cur_node = self._lsNodes.curselection()
        if len(cur_node) != 1:
            cur_node = None
        else:
            cur_node = self._lsNodes.get(cur_node)
        
        cur_option = self._int_list(self._lsListconfig.curselection())
        
        if event.widget is self._lsModules:
            if cur_module is not None:
                self._lsModules_selected(cur_module)
        elif event.widget is self._lsNodes:
            if cur_node is not None:
                self._lsNodes_selected(cur_node)
        elif event.widget is self._lsListconfig:
            print("curr options", cur_option)
            self._lsListconfig_selected(cur_option)
    
    def _testbox_event_handler(self, event):
        #maybe the rstrip is bad...
        text =  self._txTextconfig.get("1.0", tkinter.END).rstrip('\n')
        self._ctrl.setChoice(text)
    
    def initModules(self, names):
        """Sets up the list of modules
        
        Will be called by the controller if a new set of modules
        has been loaded.
        :param names: Module names that will be shown in list.
        """
        self._reset_listbox(self._lsModules)
        self._reset_listbox(self._lsNodes)
        self._reset_config()
        for mod_name in names:
            self._lsModules.insert(tkinter.END, mod_name)
    
    def initNodes(self, nodes, colors):
        """Initializes nodes list.
        
        Will be called by the controller if a new module has been chosen
        to configure.
        
        :param nodes:  Nodes of the current modules. (Just names)
        :param colors: Colors of nodes. The size of this iterable 
                       container has to be the same as the size 
                       of *nodes*
        """
        self._reset_listbox(self._lsNodes)
        self._reset_config()
        
        for index in range(len(nodes)):
            self._lsNodes.insert(tkinter.END, nodes[index])
            self._lsNodes.itemconfig(str(index)
                 , foreground=colors[index])
    
    def updateNodes(self, nodes, colors):
        """Updates nodes list and colors (_lsNodes).
        
        :param nodes:  List of current nodes that shall be shown.
        :param colors: Colors of all nodes. The size of this iterable 
                       container has to be the same as the size 
                       of *nodes*
        """
        cur_node = self._lsNodes.curselection()
        
        elm = self._lsNodes.get("0", tkinter.END)
        max = len(elm) - 1
        for (i, v) in enumerate(reversed(elm)):
            if v not in nodes:
                self._lsNodes.delete(str(max - i))
        
        for v in nodes:
            if v not in elm:
                self._lsNodes.insert(tkinter.END, v)
        
        elm = self._lsNodes.get("0", tkinter.END)
        
        for (i, v) in enumerate(elm):
            ci = nodes.index(v)
            self._lsNodes.itemconfig(str(i)
                 , foreground=colors[ci])
    
    def _reset_listbox(self, lstbox):
        lstbox.selection_clear("0", tkinter.END)
        lstbox.delete("0", tkinter.END)
    
    def _reset_config(self):
        self._txTextconfig.config(state='normal')
        self._txTextconfig.delete("1.0", tkinter.END)
        self._reset_listbox(self._lsListconfig)
        self._lsListconfig.config(state='disabled')
        self._txTextconfig.config(state='disabled')
        self._butApply.config(state='disabled')
        self._butReset.config(state='disabled')
    
    def _enable_config_buttons(self):
        self._butApply.config(state='normal')
        self._butReset.config(state='normal')
    
    def _copy_config_list(self, lst):
        for elm in lst:
            self._lsListconfig.insert(tkinter.END, elm)
    
    def setModuleHelp(self, text):
        """Just sets text of _labModules control.
        
        :param text: Text that shall be displayed next to _lsModules.
                     Normally this will be some basic information 
                     about the currently selected module.
        """
        self._labModules.config(text=text)
    
    def setNodeHelp(self, text):
        """Just sets text of _labNodes control.
        
        :param text: Text that shall be displayed next to _lsNodes.
                     Normally this will be the *help* member of
                     the currently selected node.
        """
        self._labNodes.config(text=text)
    
    def setConfigHelp(self, text):
        # Not implemented yet...
        pass
    
    def setTextNode(self, choice):
        """Sets up gui for a text-based node.
        
        If some text-like (that means not list-like or constant)
        node will be selected, the controller should call this 
        method to configure the gui to let the user enter some 
        text or expression.
        :param choice: The configured value (or None).
        """
        self._reset_config()
        self._enable_config_buttons()
        self._txTextconfig.config(state='normal')
        if choice is not None:
            self._txTextconfig.insert(tkinter.END, choice, 'sel')
            self._root.after(10, self._txTextconfig.focus_force)
    
    def setConstNode(self, choice):
        """Sets up the gui to just show the current choice.
        
        Will only show the current value and not let the user
        configure it's value.
        
        :param choice: Current value or None if not set.
        """
        self._reset_config()
        self._txTextconfig.config(state='normal')
        if choice is not None:
            self._txTextconfig.insert(tkinter.END, choice, 'sel')
        self._txTextconfig.config(state='disabled')
    
    def setListNode(self, lst, choice):
        """Sets up the gui to allow the user to choose from a list.
        
        :param lst:     The list of possible choices.
        :param choice:  The current choice (or None if no choice has
                        been made).
        """
        self._reset_config()
        self._enable_config_buttons()
        self._lsListconfig.config(state='normal', selectmode='single')
        self._copy_config_list(lst)
        if choice is not None:
            self._lsListconfig.selection_set(str(choice))
    
    def setMultiNode(self, lst, choice):
        """Sets up the gui to allow the user to choose multiple values.
        
        Will be called if a multi list node has been chosen.
        
        :param lst:     The list of possible choices.
        :param choice:  The current choice (or None if no choice has 
                        been made).
        """
        self._reset_config()
        self._enable_config_buttons()
        self._lsListconfig.config(state='normal', selectmode='multiple')
        self._copy_config_list(lst)
        if choice is not None:
            for index in choice:
                self._lsListconfig.selection_set(str(index))
    
    def mainloop(self):
        """Runs the tk event loop
        
        This starts a infinite loop until the user presses ok, cancel
        or closes the window.
        """
        self._root.mainloop()


if __name__ == '__main__':
    gui = Pbgui()
    gui.mainloop()
