import os
import re
import sys
import shlex
import collections
from warnings import warn
from optparse import OptionParser
import plog
import targets
import puser
from pexcept import NotYetWorkingWarning

# node types:
NT_TEXT = 'text'
NT_LIST = 'list'
NT_MULTI = 'multi'
NT_CONST = 'value'

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


class BasicNode(object):
    """This is the root of all nodes and covers the very basics.
    
    All node typs are derived from this one. It covers basic features
    like help text, status, flags and override support.
    """
    
    CONFIGURED = 1
    
    _log = plog.clone_system_logger(_PLOG_NAME)
    __slots__ = ('_name', '_overrider', '_help', '_flags', '_iseeker'
               , '_status', '_value', '_unresolved_flags')
    
    def __init__(self, name, help=None, flags=None, **kgs):
        """Creates a new node with name 'name'.
        
        @param name:  Name of this Node.
        @param help:  Optional help messages.
        @param flags: Flags which have to be true to enable this
                      node. Note that flags are always automatically
                      added to deps (sine this node depends on them).
        """
        self._name = name
        self._overrider = None
        self._iseeker = set()
        self._status = 0
        self._value = None
        
        if help is None:
            self._help = ""
        else:
            self._help = help
        
        self._flags = set()
        
        if flags is None:
            self._unresolved_flags = set()
        else:
            self._unresolved_flags = set(flags)
    
    def getNodeType(self):
        pass
    
    def getName(self):
        """This method returns the name of this node.
        
        @returns: Returns the name of this node.
        """
        return self._name
    
    def registerOverride(self, node):
        """This method has to be called to override a node.
        
        There can only be one node that overrides this one.
        TODO: Should throw an Exception if overriding fails.
        
        @param node: Node that configures this node.
        """
        if self._overrider is not None:
            print("change that!")
            raise TypeError("Wrong Exception Type for failed override...")
        else:
            self._overrider = node
            node.addInfoSeeker(self)
            self.update()
    
    def resolveFlags(self, mod):
        """This method resolves flags.
        
        @param mod: module node that is needed to resolve.
        """
        for flag in self._unresolved_flags:
            if not isinstance(flag, BasicNode):
                flag_node = mod.getNode(flag)
                self._flags.add(flag_node)
                flag_node.addInfoSeeker(self)
    
    def isOverriden(self):
        """This method returns if this node is overriden.
        @returns: True if this one is overriden.
        """
        if self._overrider is None:
            return False
        else:
            return True
    
    def isDisabled(self):
        """This method checks if the current node is disabled.
        
        Being disabled means that the input of this node is not needed.
        
        @returns: Returns True if this node really is disabled,
                  else False.
        """
        for flag in self._flags:
            if flag.isConfigured:
                if not flag.readValue():
                    return True
            else:
                return True
        return False
    
    def isConfigured(self):
        """This method checks if a value has been configured
        
        @returns: Returns True if value has been configured, else
                  False.
        """
        return (self._status & self.CONFIGURED == self.CONFIGURED)
    
    def readValue(self, **ignore):
        """Reads configuration an returns value
        @param ignore: Ignored arguments used for compatiblity
                       with BasicChoice
        @returns:      Returns value.
        """
        return self._value
    
    def addInfoSeeker(self, seeker):
        """This method add a node that needs the input of this node.
        
        @param node: The node that want to be notified if this one 
                     will be set up.
        """
        self._iseeker.add(seeker)
    
    def notifyInfoSeeker(self):
        
        for seeker in self._iseeker:
            seeker.update()
    
    def update(self):
        
        if self._overrider:
            self._status = self._overrider._status
            self._value = self._overrider._value
    
    def isLike(self, node):
        return (self.getNodeType() == node.getNodeType())


class BasicChoice(BasicNode):
    """This is the root node, which covers basic properties.
    
    All node typs are derived from this one. It covers basic features
    like handle dependencies (nodes, that have to be set up before
    this one can be configured), flags (can be used to disable 
    many settings at once), help message, format function,
    check function etc...
    """
    
    __slots__ = ('_name', '_format')
    
    def __init__(self, name, check=None, format=None, **kgs):
        """Creates a new node with name 'name'.
        
        @param name:    Name of this node.
        @param check:   A check method (checks applied value).
        @param format:  This method formats the actual value.
        @param kgs:     Collects unsupported arguments.
        """
        BasicNode.__init__(self, name, **kgs)
        self._check = check
        self._format = format
    
    def readValue(self, formatted=False):
        """Reads configuration an returns value
        
        @param formatted: If formatted is True, the current value will
                          be formatted by the format method 
                          (see __init__).
        @returns: Returns value.
        """
        value = BasicNode.readValue(self)
        if formatted and isinstance(self._format, collections.Callable):
            return self._format(value)
        return value
    
    def _configure_value(self, value):
        """This method just sets up the new value.
        
        It saves the new value and changes the status of this
        node to configured. It's save to call this method from
        a subclass.
        
        @param value: New value that shall be configured.
        """
        if ((value != self._value)
         or ((self._status & self.CONFIGURED) != self.CONFIGURED)):
            self._value = value
            self._status |= self.CONFIGURED
            self.notifyInfoSeeker()
    
    def setValue(self, value):
        """Configures a new value (will be overriden)
        
        @param value: New value that will be set.
        """
        if isinstance(self._check, collections.Callable):
            if self._check(value):
                self._configure_value(value)
                return True
            else:
                return False
        else:
            self._configure_value(value)
            return True


class ConstValue(BasicNode):
    
    def __init__(self, name, value, **kgs):
        
        BasicNode.__init__(self, name, **kgs)
        self._value = value
        self._status = self.CONFIGURED
    
    def getNodeType(self):
        
        return NT_CONST


class ExprChoice(BasicChoice):
    
    def __init__(self, name, **kargs):
        BasicChoice.__init__(self, name, **kargs)
    
    def getNodeType(self):
        
        return NT_TEXT


class InputChoice(BasicChoice):
    
    def __init__(self, name, **kargs):
        kargs.pop('format', None)
        self._format = self._format_value
        BasicChoice.__init__(self, name, **kargs)
    
    def _format_value(self, value):
        """This method formats 'value'
        
        It checks that no ' " ' characters mess up the string constant
        and adds them at the start and at the end of the string.
        @param value: Value to format.
        @returns:     Formatted string.
        """
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        return "".join(('"', value, '"'))
    
    def getNodeType(self):
        
        return NT_TEXT


class BasicListChoice(BasicChoice):
    
    def __init__(self, name, ilist, viewlist=None, **kargs):
        """Creates a new list node with name 'name'.
         
        @param name:     Name of node to create.
        @param ilist:    List object to choose from. Has to be a list
                         or a generator object.
        @param check:    
        @param viewlist: Optional viewlist (will be shown to the user).
        @param kargs:    Additional arguments (see BasicChoice). 
        """
        BasicChoice.__init__(self, name, **kargs)
        self._view = None
        self._list = tuple(ilist)
        
        if viewlist is not None:
            tview = list(viewlist)
            if len(self._list) == len(tview):
                self._format_view(tview)
                self._view = tuple(tview)
            else:
                warn("'%s': Length of list '%d' != viewlist '%d'."
                 % (name, len(self._list), len(tview))
                 , ViewListIgnoredWarning)
        if self._view is None:
            self._view = self._create_view_from_list()
    
    def _create_view_from_list(self):
        """Creates a sring list from self._list
        
        TODO:       Maybe I should add a type check and handle
                    dictionarys a little bit different...
        
        @returns:   Returns a tuple that contains all items of
                    self._list as string.
        """
        return tuple(str(i) for i in self._list)
    
    def _format_view(self, viewlist):
        """Creates a nice list to choose from.
        
        
        @param viewlist: The view list has got some symbolic
                         names for not easily readable values.
        @returns:        A tuple with the viewlist that will be shown
                         to the user.
        """
        for (i,v) in enumerate(viewlist):
            cur_item = str(self._list[i])
            if v is not None:
                viewlist[i] = "%s (value: %s)" % (v, cur_item)
            else:
                viewlist[i] = "(value: %s)" % cur_item
        
        return tuple(viewlist)
    
    def getViewList(self):
        """This method returns the view-list.
        
        Viewlist is a list that can be presented to the user
        see __init__ and _format_view for more information.
        
        @returns:   Returns a list that can be presented to the user.
        """
        return self._view
    
    def _get_index(self, value):
        
        for (i, v) in enumerate(self._list):
            if v == value:
                return i
        print("throw exception, or warning ListChoice.getIndex")
    
    def getList(self):
        """This method returns the real list of values that can
        be chosen.
        @returns: List of values that can be chosen.
        """
        return self._list


class ListChoice(BasicListChoice):
    
    def __init__(self, name, ilist, **kargs):
        kargs.pop('check', None)
        BasicListChoice.__init__(self, name, ilist
             , check=self._check_value, **kargs)
    
    def _check_value(self, value):
        """This method checks if self._list contains 'value'
        
        The actual choice of the user has to be on the list.
        @param value: Value to check.
        @returns:     True if value is on the list, else False.
        """
        return (value in self._list)
    
    def chooseByIndex(self, index):
        """Choose value by the index in self._list
        
        @param index: Index of element that should be configured
                      (starting from 0).
        """
        try:
            value = self._list[index]
            return self.setValue(value)
        except IndexError:
            self._log.debug("IndexError in ListChoice %s (index = %d)"
                % (self._uname, index))
    
    def getIndex(self):
        
        return self._get_index(self.readValue())
    
    def getNodeType(self):
        
        return NT_LIST


class MultiChoice(BasicListChoice):
    
    def __init__(self, name, ilist, **kargs):
        kargs.pop('check', None)
        BasicListChoice.__init__(self, name, ilist
             , check=self._check_value, **kargs)
    
    def _check_value(self, value):
        """This method checks if self._list contains 'value'
        
        The actual choice of the user has to be on the list.
        @param value: Value to check.
        @type value:  'value' is some sort of list.
        @returns:     True if all values are on the list, else False.
        """
        
        for v in value:
            if v not in self._list:
                return False
        return True
    
    def chooseIndices(self, indices):
        """Choose value by indices in self._list
        
        @param indices: Tuple of all chosen indices
                        (index starts from 0).
        """
        values = []
        try:
            for index in indices:
                value = self._list[index]
                values.append(value)
            return self.setValue(values)
        except IndexError:
            self._log.debug("IndexError in ListChoice %s (index = %d)"
                % (self._uname, index))
    
    def getIndices(self):
        
        value = self.readValue()
        indices = []
        for i in value:
            indices.append(self._get_index(i))
        return indices
    
    def getNodeType(self):
        
        return NT_MULTI


class DependencyFrame(object):
    "Contains dependent nodes."
    
    RESOLVED = 1
    AVAILABLE = 2
    NEEDEXEC = 4
    EXECUTED = 8
    
    def __init__(self, deps):
        """Initializes a new Frame.
        
        Note that this frame is not fully set up yet. It has to be
        'called' (__call__) to really be initialized.
        All dependencies (deps) have to be resolved (if they are 
        ExternalNodes.).
        @param deps: Dependencies of this frame.
        """
        self._deps = deps
        self._func = None
        self._status = self.NEEDEXEC
        self._nodes = dict()
        self._frames = set()
    
    def __call__(self, func):
        """Saves the function that will be called.
        
        TypeExcetion will be thrown if 'func' isn't callable.
        
        @param func: This function will be called if all dependencies
                     are configured.
        """
        if not isinstance(func, collections.Callable):
            raise TypeError("function (%s) isn't callable"
                 % str(func))
        else:
            self._func = func
    
    def resolveDependencies(self, mod):
        
        deps = set()
        for dep in self._deps:
            if (isinstance(dep, puser.Node)
             or isinstance(dep, puser.ExternalNode)):
                node = mod.getNode(dep)
                deps.add(node)
                node.addInfoSeeker(self)
            else:
                deps.add(dep)
        self._deps = deps
        self._status |= self.RESOLVED
    
    def addNode(self, name, node):
        
        self._nodes[name] = node
        node.addInfoSeeker(self)
    
    def addSubFrame(self, frame):
        
        self._frames.add(frame)
    
    def removeAllNodes(self, csf):
        csf.removeNodes(self._nodes.keys())
        self._nodes = dict()
    
    def removeFrames(self, csf):
        for frame in self._frames:
            frame.removeAllNodes(csf)
            frame.removeFrames(csf)
        
        csf.removeFrames(self._frames)
    
    def _is_available(self):
        for i in self._deps:
            if not i.isConfigured():
                return False
        return True
    
    def update(self):
        print("check if I'm available.", self._func.__name__)
        self._status |= self.NEEDEXEC
    
    def needsExecute(self):
        return (self._status & self.NEEDEXEC == self.NEEDEXEC)
    
    def canExecute(self):
        ret = self.needsExecute()
        ret = ret and self._is_available()
        ret = ret and ((self._status & self.RESOLVED) == self.RESOLVED)
        return ret
    
    def executeFunction(self, csf):
        """This method really executes the function (frame).
        
        All dependencies have to be configured.
        @param csf: config script file object. This class is needed
                    to install a hook that this frame will be notified
                    if a new node has been created.
        """
        # just to be sure
        if not self.canExecute():
            return None
        deps = (i.readValue() for i in self._deps)
        print("DependencyFrame status: %s" % self._status)
        csf.installHook(self)
        if self._status & self.EXECUTED:
            csf.saveAllConfig()
            self.removeAllNodes(csf)
            self.removeFrames(csf)
            
            self._frames = set()
            
            self._func(*deps)
            self._status |= (self.EXECUTED)
            self._status &= ~(self.NEEDEXEC)
        else:
            # TODO: Think about returning some value.
            self._func(*deps)
            self._status |= (self.EXECUTED)
            self._status &= ~(self.NEEDEXEC)


class ConfigScriptObj(object):
    """This class executes the configure_xxx.py file.
    
    This class handles all stuff related to the configure_xxx.py file
    (except Extension commands...).
    """
    
    def __init__(self, modnode):
        """Initializes a new instance...
        
        @param modnode: The ModuleNode that created this object.
        """
        self._mod = modnode
        self._current_frame = None
        self.nodes = None
        self.ext_write = None
        self.frames = None
        self.config = None
    
    def executeScript(self, scriptfile, config=dict()):
        """This method really runs the configure script.
        
        This should create all objects.
        @param scriptfile: Full path to the scriptfile.
        """
        self.nodes = dict()
        self.ext_write = list()
        self.frames = list()
        self.config = config
        self._current_frame = None
        
        cfg = puser.ScriptObject(self)
        env = {'__builtins__' : __builtins__,
            'PB_VERSION' : 'xxx',
            'cfg' : cfg}
        
        for (extmod, name) in self._mod.getDependencies():
            realname = extmod.uniquename()
            ext = puser.ExternalScriptObject(realname, dict())
            if name in env:
                raise InvalidUsedModNameError(
                    "'%s' is an invalid name (use extension)."
                    % name)
            env[name] = ext
        
        with open(scriptfile, 'r') as f:
            exec(compile(f.read(), '<string>', 'exec'), env, env)
    
    def _check_new_name(self, name, list_to_check=None):
        """This method checks if 'name' is in a certain list.
        
        Raises an ChoiceNodeAlreadyBoundError if the name already
        exists.
        
        @param name:          Name that should be found in some list.
        @param list_to_check: List that should be checked (if None
                              self._nodes will be checked).
        """
        if list_to_check is None:
            list_to_check = self.nodes
        if name in list_to_check:
            raise ChoiceNodeAlreadyBoundError(
                "Node '%s' has already been created (module '%s')."
                 % (name, self._mod.uniquename()))
    
    def resolveDependencies(self):
        
        for node in self.nodes.values():
            node.resolveFlags(self._mod)
        
        for frame in self.frames:
            frame.resolveDependencies(self._mod)
        
        for (ext, node) in self.ext_write:
            extmod = self._mod.getUsedModule(ext)
            i_node = extmod.getNode(ext)
            o_node = self._mod.getNode(node)
            i_node.registerOverride(o_node)
    
    def installHook(self, frame):
        """Installs a hook.
        
        Every time a new node has been created, 'frame' will be
        notified.
        @param frame: The DependencyFrame that is about ob beeing
                      executed.
        """
        self._current_frame = frame
    
    def removeNodes(self, names):
        
        for name in names:
            self.nodes.pop(name, None)
    
    def removeFrames(self, frames):
        
        for frame in frames:
            self.frames.remove(frame)
    
    def saveAllConfig(self):
        
        for (n, o) in self.nodes.items():
            if (not o.isDisabled()) and (o.isConfigured):
                self.config[n] = o.readValue()
    
    def _add_node(self, name, node):
        """This method adds a new node (internal).
        
        Note that this method only should be called if you know what
        you are doing...
        @param name: Name of new node.
        @param node: The actual node object.
        """
        
        self.nodes[name] = node
        
        if self._current_frame is not None:
            self._current_frame.addNode(name, node)
            self.resolveDependencies()
        
        if isinstance(node, BasicChoice) and (name in self.config):
            node.setValue(self.config[name])
    
    def _add_dep_frame(self, frame):
        """This method adds a new Dependency Frame (internal).
        
        @param frame: New frame to add.
        """
        self.frames.append(frame)
        
        if self._current_frame is not None:
            self._current_frame.addSubFrame(frame)
            self.resolveDependencies()
    
    def define(self, name, value, options):
        """Creates a simple constant value (C #define).
        
        @param name:    Unique (in one script) name of this node.
        @param value:   Value of this variable.
        @param options: All kinds of options.
        """
        print("define: ", name, value, options)
        self._check_new_name(name)
        self._add_node(name, ConstValue(name, value, **options))
        return puser.Node(name)
    
    def string(self, name, options):
        """String parameter will be created.
        
        (This means that '"' will be added at the begin
        and at the end of the value the user sets up)
        @param name: Unique (in one script) name of this node.
        @param options: All kinds of options (see InputChoice
                        for more information.)
        """
        print("string: ", name, options)
        self._check_new_name(name)
        self._add_node(name, InputChoice(name, **options))
        return puser.Node(name)
    
    def expr(self, name, options):
        """Expression parameter will be created.
        
        This represents only the value the user entered.
        @param name:    Unique (in one script) name of this node.
        @param options: All kinds of options (see InputChoice
                        for more information.)
        """
        print("expr: ", name, options)
        self._check_new_name(name)
        self._add_node(name, ExprChoice(name, **options))
        return puser.Node(name)
    
    def single(self, name, darray, options):
        """Single List will be created.
        
        @param name:    Unique (in one script) name of this node.
        @param darray:  Array of items to choose from.
        @param options: All kinds of options (see InputChoice
                        for more information.)
        """
        print("single: ", name, darray, options)
        self._check_new_name(name)
        self._add_node(name, ListChoice(name, darray, **options))
        return puser.Node(name)
    
    def multi(self, name, darray, options):
        """Multi List will be created.
        
        @param name:    Unique (in one script) name of this node.
        @param darray:  Array of items to choose from.
        @param options: All kinds of options (see InputChoice
                        for more information.)
        """
        print("multi: ", name, darray, options)
        self._check_new_name(name)
        self._add_node(name, MultiChoice(name, darray, **options))
        return puser.Node(name)
    
    def depends(self, deps):
        """Registers a depending function.
        
        Depending Functions are called Frames. All dependencies
        have to be configured to enable such a frame.
        
        @param deps: List of all dependencies of this Frame.
        @returns:    The newly created frame object.
        """
        frame = DependencyFrame(deps)
        self._add_dep_frame(frame)
        return frame
    
    def override(self, ext, node, options):
        """Overrides an External Node.
        
        @param ext:     External node that will be overriden.
        @param node:    Node that replaces the external node.
        @param options: All kinds of options (see InputChoice
                        for more information.)
        """
        print("override: ", ext, node, options)
        # TODO: find modulenode or raise Exception
        if (isinstance(ext, puser.ExternalNode)
         and isinstance(node, puser.Node)):
            found_module = self._mod.getUsedModule(ext)
            # TODO:
            if found_module is None:
                raise Exception("BAD")
            
            self.ext_write.append((ext, node))
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
        self._cfg = None
    
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
    
    def getDependencies(self):
        return (i for i in self._used_mods)
    
    def getUsedModule(self, name_or_node):
        """This method tries to find the external module 'name'.
        
        @param name_or_node: Unique name of the module or ExternalNode
                             (Only Module Name will be used.)
        @returns:            The module with name 'name' or None if no 
                             module exists (named 'name').
        """
        
        if isinstance(name_or_node, puser.ExternalNode):
            name = name_or_node.module
        else:
            name = name_or_node
        
        for (extmod, objname) in self._used_mods:
            if extmod.uniquename() == name:
                return extmod
        return None
    
    def getNode(self, node, inc_used=True):
        """Tries to find 'node' and returns it.
        
        @param node:     Identifies node that shall be returned.
        @type node:      Type can be puser.Node, puser.ExternalNode
                         or str (string means that it's a local node
                         -> not an external node.
        @param inc_used: If set to False, used modules will not be
                         included. (This was necessary to stop modules
                         from including used modules of their used 
                         modules and so on...
        @returns:        Returns node object.
        """
        if isinstance(node, puser.Node):
            return self._cfg.nodes[node.name]
        elif isinstance(node, puser.ExternalNode):
            if node.module == self._uname:
                return self._cfg.nodes[node.name]
            elif inc_used:
                return self.getUsedModule(node).getNode(node
                     , inc_used=False)
        elif isinstance(node, str):
            return self._cfg.nodes[node]
    
    def getNodeNames(self):
        return tuple(self._cfg.nodes.keys())
    
    def executeScript(self):
        
        cfg = ConfigScriptObj(self)
        cfg.executeScript(self._script_path)
        self._cfg = cfg
    
    def resolveNodes(self):
        
        # all modules must have been executed.
        self._cfg.resolveDependencies()
    
    def executeFrames(self):
        
        for frame in self._cfg.frames:
            frame.executeFunction(self._cfg)
    
    def generateDst(self, dst):
        pass
    
    def dump(self, file=None):
        print("module '%s':" % self._uname, file=file)
        if len(self.targets) > 0:
            print("  .target-nodes:", file=file)
        for tget in self.targets:
            print("    .dir '%s':" % tget.modulepath()
                 , file=file)
            for j in tget.iterFiles():
                print("      - '%s'" % j, file=file)
        if len(self._used_mods) > 0:
            print("  .using modules:", file=file)
        for (mod, name) in self._used_mods:
            print("    - module '%s' as '%s'"
                 % (mod.uniquename(), name), file=file)
        if self._cfg is not None:
            print ("  .nodes:", file=file)
            for node in self._cfg.nodes.values():
                name = node.getName()
                status = []
                if node.isDisabled():
                     status.append("disabled")
                if node.isConfigured():
                    status.append("configured (%s)"
                         % str(node.readValue(formatted=True)))
                else:
                    status.append("not configured")
                status.append("type='%s'" % node.getNodeType())
                print("    - node '%s':" % name, file=file)
                for i in status:
                    print("      - %s" % i, file=file)


class ModuleManager(object):
    
    _extensions = []
    
    def __init__(self, src):
        """
        @param src: The source directory where all modules
                    can be found.
        """
        self._src = src
        self._mods = dict()
        self._log = plog.clone_system_logger(_PLOG_NAME)
        self._config = dict()
        self._targets = []
    
    def loadConfig(self, config):
        """Loads a configuartion.
        
        This method just overwrites the _config 
        variable. It also iterates through all 
        modules and configures them.
        
        @param config: The config dictionary.
        """
        self._config = config
        raise NotImplementedError();
    
    def collectConfig(self):
        """Collects current configuration.
        
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
        """First loads all modules and afterwards initializes them.
        
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
        
        for (name, mod) in self._mods.items():
            mod.executeScript()
        
        for (name, mod) in self._mods.items():
            mod.resolveNodes()
    
    def _load_modules(self, targetlist, parent, directory):
        """Loads all modules.
        
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
        """Adds a new module.
        
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
    
    def getModuleNames(self):
        return tuple(self._mods.keys())
    
    def getModule(self, name):
        
        if name in self._mods:
            return self._mods[name]
        else:
            # TODO: Exception
            return None
    
    def dump(self):
        """Dumps current module-list.
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

