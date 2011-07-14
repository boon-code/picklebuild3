#!/usr/bin/env python3
""" pbgui.py --

 UI generated by GUI Builder Build 146 on 2011-02-28 14:12:40 from:
    /home/nimmer/code/picklebuild3/testgui/pbgui.ui
 This file is auto-generated.  Only the code within
    '# BEGIN USER CODE (global|class)'
    '# END USER CODE (global|class)'
 and code inside the callback subroutines will be round-tripped.
 The 'main' function is reserved.
"""

from Tkinter import *
from pbgui_ui import Pbgui

# BEGIN USER CODE global

# END USER CODE global

class CustomPbgui(Pbgui):
    pass

    # BEGIN CALLBACK CODE
    # ONLY EDIT CODE INSIDE THE def FUNCTIONS.

    # _butApply_command --
    #
    # Callback to handle _butApply widget option -command
    def _butApply_command(self, *args):
        pass

    # _butCancel_command --
    #
    # Callback to handle _butCancel widget option -command
    def _butCancel_command(self, *args):
        pass

    # _butLoadfile_command --
    #
    # Callback to handle _butLoadfile widget option -command
    def _butLoadfile_command(self, *args):
        pass

    # _butOk_command --
    #
    # Callback to handle _butOk widget option -command
    def _butOk_command(self, *args):
        pass

    # _butReset_command --
    #
    # Callback to handle _butReset widget option -command
    def _butReset_command(self, *args):
        pass

    # _butSavefile_command --
    #
    # Callback to handle _butSavefile widget option -command
    def _butSavefile_command(self, *args):
        pass

    # _lsListconfig_xscrollcommand --
    #
    # Callback to handle _lsListconfig widget option -xscrollcommand
    def _lsListconfig_xscrollcommand(self, *args):
        pass

    # _lsModules_xscrollcommand --
    #
    # Callback to handle _lsModules widget option -xscrollcommand
    def _lsModules_xscrollcommand(self, *args):
        pass

    # _lsNodes_xscrollcommand --
    #
    # Callback to handle _lsNodes widget option -xscrollcommand
    def _lsNodes_xscrollcommand(self, *args):
        pass

    # _sclListconfig_command --
    #
    # Callback to handle _sclListconfig widget option -command
    def _sclListconfig_command(self, *args):
        pass

    # _sclModules_command --
    #
    # Callback to handle _sclModules widget option -command
    def _sclModules_command(self, *args):
        pass

    # _sclNodes_command --
    #
    # Callback to handle _sclNodes widget option -command
    def _sclNodes_command(self, *args):
        pass

    # _sclTextconfig_command --
    #
    # Callback to handle _sclTextconfig widget option -command
    def _sclTextconfig_command(self, *args):
        pass

    # _txTextconfig_xscrollcommand --
    #
    # Callback to handle _txTextconfig widget option -xscrollcommand
    def _txTextconfig_xscrollcommand(self, *args):
        pass

    # END CALLBACK CODE

    # BEGIN USER CODE class

    # END USER CODE class

def main():
    # Standalone Code Initialization
    # DO NOT EDIT
    try: userinit()
    except NameError: pass
    root = Tk()
    demo = CustomPbgui(root)
    root.title('pbgui')
    try: run()
    except NameError: pass
    root.protocol('WM_DELETE_WINDOW', root.quit)
    root.mainloop()

if __name__ == '__main__': main()
