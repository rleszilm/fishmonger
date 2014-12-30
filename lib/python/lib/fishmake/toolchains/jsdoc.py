import pybase.config
import pyerl       as PyErl
import pybase.util as PyUtil
import pybase.dir  as PyDir
import os.path
import shutil

import fishmake

class ToolChain(fishmake.ToolChain):
	## Generate language specific configuration
	## Return True if we are used, false if not

	def __init__(self):
		self.extensions = ["js"]
		self.defaults   = {
			"BUILD_DIR"  : "js"
		}

	def build(self):
		pass

	def install(self):
		pass

	def installDoc(self, app):
		doc_dir = app.installDocDir("js")

		if os.path.isdir(doc_dir):
			shutil.rmtree(doc_dir)
			os.makedirs(doc_dir)

		target_files = ""
		for js_file in PyDir.findFilesByExts(["js"], app.buildDir()):
			target_file = os.path.join(app.buildDir(), js_file)
			target_files += target_file + " "

		PyUtil.shell("jsdoc -d " + doc_dir + " " + target_files, prefix="======>", stdout=True, stderr=True)