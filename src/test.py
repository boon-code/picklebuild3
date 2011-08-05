#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import targets
import pmodules
import cfgcontrol
from pbgui_imp import Pbgui

b = targets.TargetTree('../test/src/')
b.add("ha.txt", relative=True)
b.add("blop/bla.txt", relative=True)
b.add("haha/huibuh.txt", relative=True)
b.add("blala/a.txt", relative=True)
b.add("blala/b.txt", relative=True)
b.add("blop/subb/c.txt", relative=True)
b.add("blop/nsm/nsm_main.txt", relative=True)
b.add("Test/main.c", relative=True)

path = os.path.join(os.getcwd(), "../test/src")
path = os.path.normpath(path)

a = pmodules.ModuleManager('../test/src')
a.initModules(b)
a.loadNodes()
man = a
ctrl = cfgcontrol.ConfigController(Pbgui, man)
ctrl.mainloop()
print("Is fully configured: ", man.isFullyConfigured(warning=True))
