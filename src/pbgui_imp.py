#!/usr/bin/env python3
from pbgui import CustomPbgui
import tkinter

class Pbgui(CustomPbgui):
    
    def __init__(self, controller):
        root = tkinter.Tk()
        CustomPbgui.__init__(self, root)
        self._root = root
        self._ctrl = controller
        root.bind("<<ListboxSelect>>", self._listbox_event_handler)
        root.bind("<KeyRelease>", self._testbox_event_handler)
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        self._reset_last_selection()
    
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
        pass
    
    #override
    def _butSavefile_command(self, *args):
        pass
    
    #override
    def _butReset_command(self, *args):
        self._ctrl.reloadChoice()
    
    #override
    def _butApply_command(self, *args):
        print("apply: ", self._ctrl.applyChoice())
    
    def _lsNodes_selected(self, node_name):
        self._ctrl.chooseNode(node_name)
    
    def _lsModules_selected(self, mod_name):
        self._ctrl.chooseModule(mod_name)
    
    def _lsListconfig_selected(self, choice):
        self._ctrl.setChoice(choice)
    
    def _reset_last_selection(self):
        self._last_node = None
        self._last_module = None
        self._last_option = tuple()
    
    def _listbox_event_handler(self, event):
        """
        This event handler processes the <<ListboxSelect>> virtual
        event.
        @param event: Additional event arguments (Not used).
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
        
        cur_option = self._lsListconfig.curselection()
        if len(cur_option) <= 0:
            cur_option = tuple()
        else:
            cur_option = tuple(self._lsListconfig.get(i) 
                                for i in cur_option)
        try:
            #only one event can happen at one time....
            if cur_module not in (self._last_module, None):
                self._lsModules_selected(cur_module)
            elif cur_node not in (self._last_node, None):
                self._lsNodes_selected(cur_node)
            elif cur_option not in (self._last_option, None):
                self._lsListconfig_selected(cur_option)
        finally:
            self._last_module = cur_module
            self._last_node = cur_node
            self._last_option = cur_option
    
    def _testbox_event_handler(self, event):
        #maybe the rstrip is bad...
        text =  self._txTextconfig.get("1.0", tkinter.END).rstrip('\n')
        self._ctrl.setChoice(text)
    
    def initModules(self, mods):
        """
        Will be called by the controller if a new set of modules
        has been loaded.
        @param mods: Modules to add.
        """
        self._reset_listbox(self._lsModules)
        self._reset_listbox(self._lsNodes)
        self._reset_config()
        for mod in mods:
            self._lsModules.insert(tkinter.END, mod)
    
    def initNodes(self, nodes):
        """
        Will be called by the controller if a new module has been chosen
        to configure.
        @param nodes: Nodes of the module to add.
        """
        self._reset_listbox(self._lsNodes)
        self._reset_config()
        index = 0
        for node in nodes:
            self._lsNodes.insert(tkinter.END, node.getName())
            if not node.isAvailable():
                self._lsNodes.itemconfig(index, foreground='red')
            else:
                if node.isDisabled():
                    self._lsNodes.itemconfig(index, foreground='grey')
                else:
                    if node.isConfigured():
                        self._lsNodes.itemconfig(index
                            , foreground='green')
            index += 1
    
    def _reset_listbox(self, lstbox):
        lstbox.delete("0", tkinter.END)
        lstbox.selection_clear("0", tkinter.END)
    
    def _reset_config(self):
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
    
    def setTextNode(self, choice):
        """
        Will be called if a text node has been chosen.
        @param choice: The configured value (or None).
        """
        self._reset_config()
        self._enable_config_buttons()
        self._txTextconfig.config(state='normal')
        if choice is not None:
            self._txTextconfig.insert(tkinter.END, choice, 'sel')
            self._root.after(10, self._txTextconfig.focus_force)
    
    def setListNode(self, lst, choice):
        """
        Will be called if a single list node has been chosen.
        @param lst:     The list of possible choices.
        @param choice:  The current choice (or None if no choice has
                        been made).
        """
        self._reset_config()
        self._enable_config_buttons()
        self._lsListconfig.config(state='normal', selectmode='single')
        self._copy_config_list(lst)
        if choice is not None:
            if choice in lst:
                index = lst.index(choice)
                self._lsListconfig.selection_set(str(index))
            else:
                print("couldn't find '%s' in '%s'" % (choice, str(lst)))
    
    def setMultiNode(self, lst, choice):
        """
        Will be called if a multi list node has been chosen.
        @param lst:     The list of possible choices.
        @param choice:  The current choice (or None if no choice has
                        been made).
        """
        self._reset_config()
        self._enable_config_buttons()
        self._lsListconfig.config(state='normal', selectmode='multiple')
        self._copy_config_list(lst)
        if choice is not None:
            for selitem in choice:
                if selitem in lst:
                    index = lst.index(selitem)
                    self._lsListconfig.selection_set(str(index))
                else:
                    print("couldn't find '%s' in '%s'" % (selitem, str(lst)))
    
    def mainloop(self):
        """
        This starts a infinite loop until the user presses ok, cancel
        or closes the window.
        """
        self._root.mainloop()


if __name__ == '__main__':
    gui = Pbgui()
    gui.mainloop()