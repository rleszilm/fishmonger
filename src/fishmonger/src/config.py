
import pyrcs         as PyRCS
import pybase.config as PyConfig

import pybase.set    as PySet

import pybase.path   as PyPath
import pybase.find   as PyFind

import pybase.kwargs as PyKWArgs

import pybase.log    as PyLog

import os.path

import fishmonger.dirflags as DF

def dirs(ds):
	t_ds = PySet.Set(ds)
	r_ds = PySet.Set()

	for t_d in t_ds:
		r_ds.append(t_d.split(""))
	return 

class AppToolConfig(PyConfig.Config):
	class Types:
		project, app, subdir = range(0, 3)
	def __init__(self, dir, *args):

		PyLog.debug("AppToolConfig created for", dir, *args, log_level=6)
		self.type         = AppToolConfig.Types.project
		self.dependency   = False

		self._dir         = dir
		self.src_root     = dir

		self.package      = False

		self.parent       = None
		self.children     = []

		self.config       = {}

		self.defaults     = {
			"BUILD_AFTER_TOOLS" : PySet.Set(), ## ToolChains that must be run first
			"BUILD_AFTER_APPS"  : PySet.Set(), ## Apps that must be built first
			"BUILD_AFTER"       : PySet.Set(), ## Specific Tool/App pairs that must be run first

			"DEPENDENCIES"      : PySet.Set(), ## Apps in seperate repositories

			"INCLUDE_DIRS"      : PySet.Set(), ## Directories that include files reside in
			"LIB_DIRS"          : PySet.Set(), ## Directories prebuilt libraries exist in

			"DOC_DIR"           : "doc",       ## Directory to install documentation into

			"BUILD_PREFIX"      : "build",     ## Directory to place built files into
			"DEP_DIR"           : "deps",      ## Directory to checkout code into

			"INSTALL_PREFIX"    : "install",   ## Directory to install into

			"TOOL_OPTIONS"      : {},
			"TOOL_CLI_OPTIONS"  : PySet.Set(),

			"APP_OPTIONS"       : {},

			## MISC
			"SKIP_UPDATE"       : False
		}
		
		self.constants    = ["INSTALL_PREFIX"]
		
		self.types        = {
			"INCLUDE_DIRS" : PyConfig.parseDirs,
			"LIB_DIRS"     : PyConfig.parseDirs,
			"SKIP_UPDATE"  : bool
		}

		self.allowed      = {x : True for x in self.defaults}

		self.set_behavior = PyConfig.ConfigSetBehavior.merge
		self.parse(*args)

	def parse(self, env_config, tool_config, app_config):
		env_defaults  = {
			"DEPENDENCIES"      : PySet.Set(), ## Apps in seperate repositories

			"INCLUDE_DIRS"      : PySet.Set(), ## Directories that include files reside in
			"LIB_DIRS"          : PySet.Set(), ## Directories prebuilt libraries exist in

			"DOC_DIR"           : "doc",       ## Directory to install documentation into

			"INSTALL_PREFIX"    : "install",   ## Directory to install into

			"DEP_DIR"           : "deps"       ## Directory to checkout code into
		}

		tool_defaults = {
			"BUILD_AFTER_TOOLS" : PySet.Set(), ## ToolChains that must be run first

			"INCLUDE_DIRS"      : PySet.Set(), ## Directories that include files reside in
			"LIB_DIRS"          : PySet.Set(), ## Directories prebuilt libraries exist in

			"DOC_DIR"           : "doc",       ## Directory to install documentation into
			"BUILD_PREFIX"      : "build",     ## Directory to place built files into

			"TOOL_CLI_OPTIONS"  : PySet.Set(),

			"TOOL_OPTIONS"      : {}
		}

		app_defaults  = {
			"BUILD_AFTER_APPS"  : PySet.Set(), ## Apps that must be built first
			"BUILD_AFTER"       : PySet.Set(), ## Specific Tool/App pairs that must be run first

			"DEPENDENCIES"      : PySet.Set(), ## Apps in seperate repositories
			
			##
			"INCLUDE_DIRS"      : PySet.Set(), ## Directories that include files reside in
			"LIB_DIRS"          : PySet.Set(), ## Directories prebuilt libraries exist in
			
			"DOC_DIR"           : "doc",       ## Directory to install documentation into
			"BUILD_PREFIX"      : "build",     ## Directory to place built files into
			
			"APP_OPTIONS"       : {}           ## Free space. Used by tool chain to
		}

		env_allowed    = {x : True for x in env_defaults.keys()}
		tool_allowed   = {x : True for x in tool_defaults.keys()}
		app_allowed    = {x : True for x in app_defaults.keys()}

		env_constants  = ["INSTALL_PREFIX"]
		tool_constants = []
		app_constants  = []


		t_env_config   = PyConfig.Config(defaults=env_defaults, allowed=env_allowed, types=self.types, constants=env_constants)
		t_env_config.safeMerge(env_config)
		
		t_tool_config  = PyConfig.Config(defaults=tool_defaults, allowed=tool_allowed, types=self.types, constants=tool_constants)
		if tool_config != None:
			t_tool_config.safeMerge(tool_config)
		
		t_app_config   = PyConfig.Config(defaults=app_defaults, allowed=app_allowed, types=self.types, constants=app_constants)
		if app_config != None:
			t_app_config.safeMerge(app_config)
		
		self.safeMerge(t_env_config)
		self.safeMerge(t_tool_config)
		self.safeMerge(t_app_config)
		self.safeMerge(PyConfig.CLIConfig())

	def mergeIfNull(self, values):
		for key in values:
			if key not in self.config:
				self.config[key] = values[key]
			elif isinstance(self.config[key], dict) and isinstance(values[key], dict):
				PyUtil.mergeDicts(self.config[key], values[key])

	#def inpath(self, *args, **kwargs):
	#	kwargs["use_prefix"] = False
	#	return self.__path(*args, **kwargs)

	#def outpath(self, *args, **kwargs):
	#	kwargs["use_prefix"] = True
	#	return self.__path(*args, **kwargs)

	def path(self, options=0, dirs=[], subdirs=[], file_name=None, lang=None, relative_to=None):
		## Check for validity
		prefix   = self.getPrefix(options)
		dir_name = self.getDirName(options, lang)

		d = self.makeDir(prefix, dirs, dir_name, subdirs, file_name, options, relative_to)
		PyLog.debug("Generated dir", d, log_level=8, **{"options":options, "dirs":dirs, "subdirs":subdirs, "file_name":file_name, "lang":lang})
		return d

	def howManyBitsSet(self, start, count, bits):
		values = [1 << d for d in range(start, start+count)]
		found  = 0
		for v in values:
			if ((bits & v) != 0):
				found += 1
		return found

	def getPrefix(self, options):
		found = self.howManyBitsSet(0, 3, options)

		if found == 0:
			raise "One of source|build|install must be set."
		if found > 1:
			raise "Only one of source|build|install may be set."
		
		prefix = None
		if options & DF.source:
			prefix = self._dir
		elif options & DF.build:
			prefix = self["BUILD_PREFIX"]
		elif options & DF.install:
			prefix = self["INSTALL_PREFIX"]

		if not options & DF.source and self.package:
			prefix = os.path.join("package", prefix)

		return prefix

	def getDirName(self, options, lang):
		found = self.howManyBitsSet(3, 9, options)

		if found == 0:
			raise "None found; One of bin|doc|etc|langlib|lib|sbin|var must be set."
		if found > 1:
			raise "Multiple found; Only one of bin|doc|etc|langlib|lib|sbin|var may be set."
		
		app     = True if options & DF.app     else False
		version = True if options & DF.version else False

		dir_name = None
		if   options & DF.bin:
			dir_name = "bin"
		elif options & DF.doc:
			dir_name = "doc"
		elif options & DF.etc:
			dir_name = "etc"
		elif options & DF.langlib:
			if lang == None:
				raise "lang must be specified for langlib"
			dir_name = "lib/" + lang + "/lib"
		elif options & DF.lib:
			dir_name = "lib"
		elif options & DF.root:
			dir_name = ""
		elif options & DF.sbin:
			dir_name = "sbin"
		elif options & DF.src:
			if not os.path.isdir(os.path.join(self._dir, "src")):
				dir_name = ""
			else:
				dir_name = "src"
		elif options & DF.var:
			dir_name = "var"
			
		if app:
			if version:
				return os.path.join(dir_name, self.name() + "-" + PyRCS.getVersion(self._dir))
			return os.path.join(dir_name, self.name())
		return dir_name

	def makeDir(self, prefix, dirs, dir_name, subdirs, file_name, options, relative_to):
		_dir = prefix
		for d in dirs:
			_dir = os.path.join(_dir, d)
		_dir = os.path.join(_dir, dir_name)
		for d in subdirs:
			_dir = os.path.join(_dir, d)
		if file_name != None:
			_dir = os.path.join(_dir, file_name)

		if _dir[-1:] == "/":
			_dir = _dir[:-1]

		found = self.howManyBitsSet(14, 2, options)
		if found == 2:
			raise "Cannot specify absolute AND relative"

		if (DF.absolute & options) == DF.absolute:
			return PyPath.makeAbsolute(_dir)
		if (DF.relative & options) == DF.relative:
			if relative_to == None:
				raise "Must specify a directory to make this relative to..."
			return PyPath.makeRelative(_dir, relative_to)

		return str(_dir)

	def name(self):
		name = os.path.basename(self._dir)
		if name == ".":
			return os.path.basename(PyPath.makeAbsolute(self.src_root))
		if self.type == AppToolConfig.Types.subdir:
			return self.parent.name() + "/" + name
		else:
			return name

	def isRoot(self):
		return self.type == AppToolConfig.Types.app


class ConfigMap():
	def __init__(*args, **kwargs):
		raise PyConfig.ConfigException("ConfipMaps MUST implement init.")

	def __getitem__(self, key):
		return self.mapping[key].config

	def getNodes(self):
		return self.mapping.keys()		
	
class ConfigTree(ConfigMap):
	def __init__(self, parent=None, file=".fishmonger", dir=".", mapping=None, **kwargs):
		if mapping == None:
			mapping = {}

		self.parent     = parent
		self.dir        = dir

		mapping[dir]    = self
		dir_config      = PyConfig.FileConfig(file=os.path.join(dir, file), **kwargs)
		
		if parent:
			self.config = parent.config.clone()
			self.config.merge(dir_config)
			
		else:
			self.config = dir_config

		self.children   = [ConfigTree(parent=self, file=file, dir=d, mapping=mapping, **kwargs) for d in PyFind.getDirDirs(dir)]
		self.mapping    = mapping

	def __getitem__(self, key):
		return self.mapping[key].config

	def getNodes(self):
		return self.mapping.keys()

class ConfigPath(ConfigMap):
	def __init__(self, parent=None, file=".fishmonger", root=".", path=".", mapping={}, **kwargs):
		path            = PyPath.makeRelative(path, root)
		self.mapping    = {}

		t_path = ""
		parent = None
		for dir in path.split("/"):
			t_path = os.path.join(t_path, dir)
			dir_config  = PyConfig.FileConfig(os.path.join(t_path, file), **kwargs)

			if parent:
				self.mapping[t_path] = parent.config.clone()
				self.mapping[t_path].merge(dir_config)
			else:
				parent               = dir_config
				self.mapping[t_path] = dir_config

	def __getitem__(self, key):
		return self.mapping[key]
