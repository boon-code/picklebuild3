import os
import re
import sys
import shlex
from warnings import warn
from optparse import OptionParser
import plog
import targets
import puser
from pexcept import NotYetWorkingWarning

# choice types:
CT_TEXT = 'text'
CT_LIST = 'list'
CT_MULTI = 'multi'

# just for logging
_PLOG_NAME = 'modules'

# regular expressions for matching configure scripts
_CFG_SCRIPTFILE_RE = re.compile("^configure_([^\\s]+)[.]{1}py$")
_CFG_SCRIPTFILE = "configure_%s.py"
_CFG_EXTENSION_RE = re.compile("^\\s*#\\$\\s+" + 
    "([^\\n,^\\r]+)\\r{0,1}\\n{0,1}\\r{0,1}$")

# extension commands:
_EXTENSION_USE = ('use', 'using')
_EXTENSION_EXT = ('ext', 'extension')

# debug, warning and error messages:
_CRITICAL_MODULE_NAME_NOT_UNIQUE = ("I have already found a module"
    + " with name '%s'.")
_INFO_MODULE_ALREADY_FOUND = ("Already listed this module: %s."
    + " Will be ignored.")
_DBG_EXTENSION_FOUND = "Module '%s': Found Extension '%s'"
_WARN_UNKNOWN_EXTENSION = ("Unknown extension command ('%s') found."
    + " Will be ignored.")
_WARN_EXC_EXT_FAILED = "Couldn't exec extension '%s' (args: '%s')."
_WARN_EXT_NOT_YET_WORKING = "The extension '%s' is not yet implemented."
_CRITICAL_MODULE_NOT_INITIALIZED = ("Module '%s' hasn't been "
    + "initialized. Can't return path.")


class ModuleException(Exception):
    pass


class MoreThanOneModuleError(ModuleException):
    
    def __init__(self, directory, module_names=None):
        ModuleException.__init__(self)
        self.directory = directory
        self.module_names = module_names


class ModuleNameAlreadyUsedError(ModuleException):
    
    def __init__(self, name, paths=[]):
        ModuleException.__init__(self)
        self.paths = paths
        self.name = name


class InvalidUsedModNameError(ModuleException):
    pass


class ChoiceNodeAlreadyBoundError(ModuleException):
    pass


class ExtensionWarning(UserWarning):
    pass


class ViewListIgnoredWarning(UserWarning):
    pass


def _unique_name(name):
    """Creates a unique module (or node) name.
    
    Basically it just returns an uppercase version.
    @param name: The name to process.
    """
    return name.strip().upper()


class BasicChoice(object):
    """This is the root node, which covers basic properties.
    
    All node typs are derived from this one. It covers basic features
    like handle dependencies (nodes, that have to be set up before
    this one can be configured), flags (can be used to disable 
    many settings at once), help message, format function,
    check function etc...
    """
    
    ENABLED = 1
    AVAILABLE = 2
    CONFIGURED = 4
    
    def __init__(self, name, check=None, format=None, help=None,
        deps=None, flags=None, **kgs):
        """Creates a new node with name 'name'.
        
        @param name:    Name of this node.
        @param check:   A check method (checks applied value).
        @param format:  This method formats the actual value.
        @param help:    Optional help text.
        @param deps:    Dependencies of this node.
        @param flags:   Flags which have to be true to enable this
                        node. Note that flags are always automatically
                        added to deps (sine this node depends on them).
        @param kgs:     Collects unsupported arguments.
        """
        self._name = name
        self._check = check
        self._format = format
        self._help = help
        self._iseeker = set()
        # configured value
        self._value = None
        self._status = 0
        
        if deps is None:
            self._deps = set()
        else:
            self._deps = set(deps)
        
        if flags is None:
            self._flags = set()
        else:
            self._flags = set(flags)
            self._deps.update(self._flags)
        # TODO: maybe I should check type...
        for dep in self._deps:
            dep._add_info_seeker(self)
    
    def _add_info_seeker(self, node):
        """This method add a node that needs the input of this node.
        
        Note that this method has got a side effect on flags! 'node'
        has to derive flags of it's 'parent'.
        @param node: The node that want to be notified if this one 
                     will be set up.
        """
        self._iseeker.add(node)
        node._derive_flags(self._flags)
    
    def _derive_flags(self, flags):
        """This method adds 'flags' to this node
        
        This will only be used by this class to derive parent flags.
        Deriving flags is necessary to disable all depending nodes
        (since they can never be resolved).
        """
        self._flags.update(flags)
    
    def updateStatus(self):
        """This method updates the current state of this node
        
        (Maybe it got available or disabled...)
        Will be called by a node that knows that this node depends
        on it if the first node has been configured.
        """
        status = (self._status & self.CONFIGURED)
        if self._is_available():
            status |= self.AVAILABLE
            if not self._is_disabled():
                status |= self.ENABLED
        
        if self._status != status:
            self._status = status
            # notify interessted class
    
    def _is_available(self):
        """This method checks, if this node is available.
        
        Being available means, that all nodes in self._deps have
        been configured properly.
        
        @returns: True if this node is available, else False.
        """
        for node in self._deps:
            # check if nodes are configured
            if not node.isConfigured():
                return False
        return True
    
    def _is_disabled(self):
        """This method checks if the current node is disabled.
        
        Being disabled means that the input of this node is not needed.
        Therefore this can't be evaluated before all dependencies are
        resolved, thus the node has to be available.
        
        Important: User of this method has to ensure, that this node
        is available! Don't use this method directly if you don'T know
        what you are doing. Use updateStatus instead and call
        getStatus() afterwards.
        
        @returns: Returns True if this node really is disabled,
                  else False.
        """
        for flag in self._flags:
            if not flag.readValue():
                return True
        return False
    
    def isConfigured(self):
        """This method checks if a value has been configured
        
        @returns: Returns True if value has been configured, else
                  False.
        """
        if self._status & self.CONFIGURED:
            return True
        else:
            return False
    
    def getStatus(self):
        """This method returns the current status.
        
        Important: Status will not be updated first!
        You have to call updateStatus() first, if you want to be sure
        to get the most recent status (But this class is intend to 
        update the status on it'S own, so getStatus should always
        return the most recent status!
        
        @returns: Current status of this node.
        """
        return self._status
    
    def isAvailabe(self):
        """This method returns if this node is available
        
        It just reads _status and checks if the available bit is set.
        """
        if self._status & self.AVAILABLE:
            return True
        else:
            return False
    
    def isDisabled(self):
        """This method returns if this node is disabled
        
        It just reads _status and checks if the enabled bit is set.
        @returns: Returns True if node is disabled.
        """
        if self._status & self.ENABLED:
            return False
        else:
            return True
    
    def readValue(self):
        pass
    
    def getName(self):
        """This method returns the name of this node.
        
        @returns: Returns the name of this node.
        """
        return self._name


class ExprChoice(BasicChoice):
    
    def __init__(self, name, **kargs):
        BasicChoice.__init__(self, name, **kargs)


class InputChoice(BasicChoice):
    
    def __init__(self, name, **kargs):
        BasicChoice.__init__(self, name, **kargs)


class BasicListChoice(BasicChoice):
    
    def __init__(self, name, ilist, viewlist=None, **kargs):
        """
        Creates a new instance. 
        @param name:     Name of node to create.
        @param ilist:    List object to choose from. (Can also
                         be an ExternalNode, or an BasicListChoice)
        @param viewlist: Optional viewlist (will be shown to the user).
        @param kargs:    Additional arguments (see BasicChoice). 
        """
        BasicChoice.__init__(self, name, **kargs)
        self._is_external = False
        self._view = None
        self._list = ilist
        self._needs_resolve = False
        
        is_external = isinstance(ilist, puser.ExternalNode)
        is_listch = isinstance(ilist, BasicListChoice)
        
        if is_external or is_listch:
            if viewlist is not None:
                warn("'%s': ilist is a node -> viewlist must be None."
                     % name, ViewListIgnoredWarning)
            self._needs_resolve = True
            raise NotYetWorkingWarning("Not yet implemented...")
        else:
            self._list = tuple(ilist)
            if viewlist is None:
                self._view = self._list
            else:
                tview = list(view)
                if len(self._list) == len(tview):
                    self._format_view(tview)
                    self._view = tuple(tview)
                else:
                    warn("'%s': Length of list '%d' != viewlist '%d'."
                     % (name, len(tlist), len(tview))
                     , ViewListIgnoredWarning)
                    self._view = self._list
    
    def _format_view(self, view):
        
        for (i,v) in enumerate(view):
            if v is not None:
                cur_item = str(self_list[i])
                view[i] = "%s (value: %s)" % (v, cur_item)
            else:
                view[i] = self._list[i]


class ListChoice(BasicListChoice):
    
    def __init__(self, name, ilist, **kargs):
        BasicListChoice.__init__(self, name, ilist, **kargs)


class MultiChoice(BasicListChoice):
    
    def __init__(self, name, ilist, **kargs):
        BasicListChoice.__init__(self, name, ilist, **kargs)


class BoundChoice(BasicChoice):
    
    def __init__(self, name, func, deps, **kargs):
        BasicChoice.__init__(self, name, **kargs)
        self._func = func
        self._deps = deps
    
    def register_dependencies(self, nodes):
        """
        This method registers all dependencies of this node
        (Which means all nodes that have to be setup before this
        one can be processed)
        @param nodes: The list of all nodes of the module that
                      include this node.
        """
        
        pass


class ExtOverrideChoice(BasicChoice):
    """
    This class will be used to identify an overridden choice.
    """
    
    def __init__(self, name, mod, func, deps, **kargs):
        BasicChoice.__init__(self, name, **kargs)
        self._func = func
        self._ext_mod = mod
        self._deps = deps


class ExtReadChoice(object):
    
    def __init__(self, name, mod):
        self._name = name
        self._mod = mod
        self._res_node = None


class ScriptFileManager(object):
    
    def __init__(self, mod):
        self._mod = mod
        self._nodes = None
        self._used = None
        self._ext_read = None
        self._ext_write = None
    
    def execute_script(self, scriptfile):
        
        self._nodes = dict()
        self._used = list()
        self._ext_read = dict()
        self._ext_write = dict()
        
        cfg = puser.ScriptObject(self)
        env = {'__builtins__' : __builtins__,
            'PB_VERSION' : 'xxx',
            'cfg' : cfg}
        
        for (extmod, name) in self._mod.get_dependencies():
            realname = extmod.uniquename()
            ext = puser.ExternalScriptObject(realname, dict())
            self._used.append(extmod)
            if name in env:
                raise InvalidUsedModNameError(
                    "'%s' is an invalid name (use extension)."
                    % name)
            env[name] = ext
        
        with open(scriptfile, 'r') as f:
            exec(compile(f.read(), '<string>', 'exec'), env, env)
    
    def _check_new_name(self, name, list_to_check=None):
        if list_to_check is None:
            list_to_check = self._nodes
        if name in list_to_check:
            raise ChoiceNodeAlreadyBoundError(
                "Node '%s' has already been created (module '%s')."
                 % (name, self._mod.uniquename()))
    
    def _resolve_deps(self, deps):
        
        int_deps = []
        ext_deps = []
        for i in deps:
            if isinstance(i, puser.Node):
                name = i.name
                if name in self._nodes:
                    int_deps.append(self._nodes[name])
                else:
                    # TODO:
                    raise Exception("Couldn't find")
            elif isinstance(i, puser.ExternalNode):
                mod_name = i.module
                    
    def _find_ext_mod(self, name):
        
        for (extmod, objname) in self._mod.get_dependencies():
            if extmod.uniquename() == name:
                return extmod
        return None
    
    def string(self, name, options):
        """
        String parameter will be created.
        (This means that '"' will be added at the begin
        and at the end of the value the user sets up)
        @param name: Unique (in one script) name of this node.
        @param options: All kinds of options (see InputChoice
                        for more information.)
        """
        print("string: ", name, options)
        self._check_new_name(name)
        self._nodes[name] = InputChoice(name, **options)
        return puser.Node(name)
    
    def expr(self, name, options):
        """
        Expression parameter will be created.
        This represents only the value the user entered.
        @param name: Unique (in one script) name of this node.
        @param options: All kinds of options (see InputChoice
                        for more information.)
        """
        print("expr: ", name, options)
        self._check_new_name(name)
        self._nodes[name] = ExprChoice(name, **options)
        return puser.Node(name)
    
    def single(self, name, darray, options):
        """
        
        """
        print("single: ", name, darray, options)
        self._check_new_name(name)
        self._nodes[name] = ListChoice(name, darray, **options)
        return puser.Node(name)
    
    def multi(self, name, darray, options):
        print("multi: ", name, darray, options)
        self._check_new_name(name)
        self._nodes[name] = MultiChoice(name, darray, **options)
        return puser.Node(name)
    
    def bind(self, name, func, deps, options):
        print("bind: ", name, func, deps, options)
        self._check_new_name(name)
        self._nodes[name] = BoundChoice(name, func, deps, **options)
        return puser.Node(name)
    
    def override(self, ext, func, deps, options):
        print("override: ", ext, func, deps, options)
        # TODO: find modulenode or raise Exception
        if isinstance(ext, puser.ExternalNode):
            name = "%s-%s" % (ext.module, ext.name)
            self._check_new_name(name, list_to_check=self._ext_write)
            
            for (extmod, name) in self._mod.get_dependencies():
                if extmod.uniquename() == name:
                    found_module = extmod
            found_module = self._find_ext_mod()
            
            # TODO:
            if found_module is None:
                raise Exception("BAD")
            
            self._ext_write[name] = ExtOverrideChoice(ext.name
                , found_module, func, deps, **options)
        else:
            raise TypeError(
                "First parameter of override expects an ExternalNode")


class ModuleNode(object):
    
    def __init__(self, src, relpath, name):
        
        self._rpath = relpath
        self._uname = _unique_name(name)
        self._realname = name
        self._basepath = os.path.join(src, relpath)
        self._log = plog.clone_system_logger(_PLOG_NAME)
        self._script_path = None
        self._used_mods = []
        # Will (directly) be used by ModuleManager
        self.targets = []
    
    def uniquename(self):
        return self._uname
    
    def relativepath(self):
        """
        This method returns the relative path to this module directory
        (relative to src).
        
        @returns: The relative path to this module (relative to src).
        """
        return self._rpath
    
    def fullpath(self):
        """
        This method returns the full path.
        @returns: Full path.
        """
        return os.path.realpath(self._basepath)
    
    def initialize(self, src, mods):
        """
        This method initializes this module.
        (which means parsing the script file and executing 
        the extension script)
        @param src:   Source directory (relative).
        @param mods:  A dictionary of all modules that have been found.
        """
        self._script_path = os.path.join(self._basepath
            , _CFG_SCRIPTFILE % self._realname)
        commands = self._parse_extensions()
        
        for tup in commands:
            cmd, args = tup
            self._execute_ext_cmd(cmd, args, mods)
    
    def _parse_extensions(self):
        
        with open(self._script_path, 'r') as scriptfile:
            extcmds = []
            for line in scriptfile:
                ext_match = _CFG_EXTENSION_RE.match(line)
                if ext_match is not None:
                    cmd = ext_match.group(1)
                    self._log.debug(_DBG_EXTENSION_FOUND
                         % (self._uname, cmd))
                    args = shlex.split(cmd)
                    if len(args) > 0:
                        extcmds.append((args[0], args[1:]))
                    else:
                        warn("Module '%s': Dropping " +
                            + "extension '%s'. "
                            + "Invalid argument (missing?)."
                            % cmd, ExtensionWarning)
            return extcmds
    
    def _execute_ext_cmd(self, cmd, args, mods):
        
        ret = False
        if cmd in _EXTENSION_USE:
            ret = self._do_ext_use(args, mods)
        elif cmd in _EXTENSION_EXT:
            #TODO: implement!
            warn(_WARN_EXT_NOT_YET_WORKING % cmd, NotYetWorkingWarning)
            ret = False
        else:
            warn(_WARN_UNKNOWN_EXTENSION % cmd, ExtensionWarning)
        
        if not ret:
            warn(_WARN_EXC_EXT_FAILED % (cmd, args)
                 , ExtensionWarning)
    
    def _do_ext_use(self, args, mods):
        
        parser = OptionParser(add_help_option=False)
        parser.add_option("-n", "--name", help="Name of module")
        parser.set_defaults(name=None)
        options, args = parser.parse_args(args)
        
        if len(args) == 1:
            mname = _unique_name(args[0])
            if (mname is not self._uname) and (mname in mods):
                mod = mods[mname]
                if options.name is not None:
                    mname = options.name
                self._used_mods.append((mod, mname))
                return True
        return False
    
    def get_dependencies(self):
        return (i for i in self._used_mods)
    
    def execute_script(self):
        
        sman = ScriptFileManager(self)
        sman.execute_script(self._script_path)
    
    def generate_dst(self, dst):
        pass
    
    def dump(self, file=None):
        print("module '%s':" % self._uname, file=file)
        if len(self.targets) > 0:
            print("  .target-nodes:", file=file)
        for tget in self.targets:
            print("    .node '%s':" % tget.modulepath()
                 , file=file)
            
            for j in tget.iterFiles():
                print("      - '%s'" % j, file=file)
        if len(self._used_mods) > 0:
            print("  .using modules:", file=file)
        for (mod, name) in self._used_mods:
            print("    - module '%s' as '%s'"
                 % (mod.uniquename(), name), file=file)


class ModuleManager(object):
    
    _extensions = []
    
    def __init__(self, src):
        """
        
        @param src: The source directory where all modules
                    can be found.
        """
        self._src = src
        self._mods = {}
        self._log = plog.clone_system_logger(_PLOG_NAME)
        self._config = {}
        self._targets = []
    
    def loadConfig(self, config):
        """
        This method just overwrites the _config 
        variable. It also iterates through all 
        modules and configures them.
        
        @param config: The config dictionary.
        """
        self._config = config
        raise NotImplementedError();
    
    def collectConfig(self):
        """
        This method collects the current configuration
        of all modules and returns it
        Also overwrites the _config dict.
        @return: A dictionary of all configurations of
                 all modules.
        """
        self._config = {}
        #TODO: implement...
        raise NotImplementedError()
        for (name, mod) in self._mods.items():
            self._config[name] = None
            print(name)
        
        return self._config
    
    def initModules(self, targetlist):
        """
        First loads all modules and afterwards initializes them.
        (Extension commands will be processed and connections to 
         other modules should be created here.)
        All targets will be added to the appropriate module.
        Note that modules can have sub-directories and sub-modules.
        If a sub-directory doesn't contain a configure_XXX.py script,
        it's just a sub-directory and belongs to the parent module
        (or the ModuleManager's targets list).
        
        @param targetlist: This list contains the files to 
                           add (targets).
        """
        self._load_modules(targetlist, self._targets, '.')
        for (name, mod) in self._mods.items():
            mod.initialize(self._src, self._mods)
    
    def _load_modules(self, targetlist, parent, directory):
        """
        This method will be recursively called for each subdirectory
        and load all modules found.
        @param targetlist:  This should be an instance of TreeList
                            and contain all targets.
        @param parent:      The target list of a parent module.
                            (Note that this can also be 
                             ModuleManager._targets).
        """
        directory = os.path.normpath(directory)
        path = os.path.join(self._src, directory)
        found = False
        subdirs = []
        for filename in os.listdir(path):
            fullpath = os.path.join(path, filename)
            if os.path.isdir(fullpath):
                subdirs.append(os.path.join(directory, filename))
            else:
                sf_match = _CFG_SCRIPTFILE_RE.match(filename)
                if not (sf_match is None):
                    if found:
                        self._log.critical("only one configure-script" + 
                            " per directory is allowed (%s)" % path)
                        raise MoreThanOneModuleError(path)
                    else:
                        mod = self._add_module(sf_match.group(1), directory)
                        parent = mod.targets
                        found = True
        
        targets = targetlist.getTargetNode(directory)
        if not (targets is None):
            parent.append(targets)
        
        for subs in subdirs:
            self._load_modules(targetlist, parent, subs)
    
    def _add_module(self, name, relpath):
        """
        This method trys to add a module with 'name' to the
        ModuleManager.
        @param name:    The name of the module (Note that the
                        real module name will be an uppercase version
                        of this).
        @param relpath: Relative path to this module.
        @returns:       The ModuleNode instance.
        """
        unique_name = _unique_name(name)
        new_path = os.path.realpath(os.path.join(self._src, relpath))
        
        if unique_name in self._mods:
            old_path = os.path.realpath(
                self._mods[unique_name].fullpath())
            
            if old_path != new_path:
                self._log.critical(_CRITICAL_MODULE_NAME_NOT_UNIQUE
                 % unique_name)
                raise ModuleNameAlreadyUsedError(unique_name
                    , [old_path, new_path])
            else:
                self._log.info(_INFO_MODULE_ALREADY_FOUND
                     % unique_name)
                return self._mods[unique_name]
        else:
            mod = ModuleNode(self._src, relpath, name)
            self._mods[unique_name] = mod
            self._log.debug("Added module %s (%s)."
                 % (unique_name, new_path))
            self._log.debug("Now trying to initialize '%s'."
                 % unique_name)
            return mod
    
    def dump(self):
        """
        This is just a debug method to list all found modules
        and all targets.
        """
        print("****** ModuleManager::dump() ******")
        print("ModuleManager-global-targets:")
        for i in self._targets:
            for j in i.iterFiles():
                print("    %s" % j)
        for (name, mod) in self._mods.items():
            print('')
            mod.dump()

b = targets.TargetList('../test/src')
b.add("ha.txt")
b.add("blop/bla.txt")
b.add("haha/huibuh.txt")
b.add("blala/a.txt")
b.add("blala/b.txt")
b.add("blop/subb/c.txt")
b.add("blop/nsm/nsm_main.txt")
b.add("Test/main.c")

a = ModuleManager('../test/src')
a.initModules(b)

a.dump()
a._mods['TEST'].execute_script()
