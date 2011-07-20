import targets
import pmodules

b = targets.TargetList('../test/src')
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

a.dump()
for i in a._mods:
    a._mods[i].executeScript()

c = a._mods['TEST']
c.resolveNodes()
