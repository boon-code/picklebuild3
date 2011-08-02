import targets
import pmodules
import cfgcontrol
from pbgui_imp import Pbgui

b = targets.TargetTree('../test/src')
b.add("ha.txt")
b.add("blop/bla.txt")
b.add("haha/huibuh.txt")
b.add("blala/a.txt")
b.add("blala/b.txt")
b.add("blop/subb/c.txt")
b.add("blop/nsm/nsm_main.txt")
b.add("Test/main.c")

a = pmodules.ModuleManager('../test/src')
a.initModules(b)
a.loadNodes()
man = a
ctrl = cfgcontrol.ConfigController(Pbgui, man)
print("Is fully configured: ", man.isFullyConfigured(warning=True))
