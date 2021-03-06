# -*- coding: utf-8 -*-
# @Author: xClouder
# @Date:   2017-08-26 15:13:19
# @Last Modified by:   xClouder
# @Last Modified time: 2017-09-30 18:13:33
import subprocess
import json
import os
import zipfile
import shutil
import hashlib
import json
#import zipfile

class SvnDiffWorker:
	"""Diff difference between versions"""

	def getUrl(self, baseUrl, relativeUrl, ver):

		if baseUrl.endswith("/"):
			url = baseUrl + relativeUrl
		else:
			url = baseUrl + "/" + relativeUrl

		if (ver is None):
			return url
		else:
			return url + "@" + str(ver)

	def getChangedFiles(self, oldUrl, newUrl):
		p = subprocess.Popen("svn diff --summarize %s %s | awk '/^[AM]/{print $2}'" % (oldUrl, newUrl), stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()

		if (len(output) == 0):
			print("*WARN*, diff return empty")
			return None

		filearr = output.split()
		return filearr

class SvnExporter:
	'''Export changed files to workspace'''
	def export(self, fileUrl, ver, toPath):
		print("export:" + fileUrl)
		verStr = ""
		if (ver != None):
			verStr = "-r" + str(ver)

		exportCmd = "svn export %s -q --force %s %s" % (verStr, fileUrl, toPath)
		# print("execute shell:" + exportCmd)
		p = subprocess.Popen(exportCmd, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()

class Archiver:
	def archive(self, folder, toFile):

		#make_archive把文件夹信息忽略了
		#shutil.make_archive(toFile, 'zip', folder)
		file = toFile + ".zip"
		source = folder
		ziph = zipfile.ZipFile(file, 'w', zipfile.ZIP_DEFLATED)
	    # ziph is zipfile handle
		for root, dirs, files in os.walk(source):
			ziph.write(root, os.path.relpath(root, os.path.join(source, '.')))
			for f in files:
				ziph.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), os.path.join(source, '.')))


		ziph.close()

		return file

class Reporter:
	def __init__(self):
		self.list = []

	def filesize(self, fname):
		return os.path.getsize(fname)

	def md5(self, fname):

		hash_md5 = hashlib.md5()
		with open(fname, "rb") as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash_md5.update(chunk)
		return hash_md5.hexdigest()

	def addfile(self, file, type):
		f = file
		info = {
			"type": type,
			"size": self.filesize(f),
			"md5": self.md5(f)
		}

		self.list.append(info)

	def report(self):
		# write to json
		print(json.dumps(self.list, sort_keys=True, indent=4, separators=(',', ': ')))




class BuildConfig:
	'''a class represent a build config'''
	def __init__(self, jsonData):
		self.fromUrl = jsonData["from"]
		if "fromVer" in jsonData:
			self.fromVer = jsonData["fromVer"]
		else:
			self.fromVer = None

		self.toUrl = jsonData["to"]

		if "toVer" in jsonData:
			self.toVer = jsonData["toVer"]
		else:
			self.toVer = None

		self.archivePath = jsonData["archivePath"]
		self.modules = jsonData["modules"]

class HotfixModule:
	'''a module to hotfix, like Table, Lua, DLL.ex'''
	def __init__(self, name, relativePath, config):
		self.name = name
		self.relativePath = relativePath
		self.config = config

	def _geturl(self, diffedUrl, newTargetBaseUrl, moduleRelativePath):
		index = diffedUrl.find(moduleRelativePath)
		if (index < 0):
			return None
		else:
			if newTargetBaseUrl.endswith('/'):
				base = newTargetBaseUrl
			else:
				base = newTargetBaseUrl + "/"

			return base + diffedUrl[index:]

	def _getpath(self, exportUrl, moduleRelativePath, archivePath):
		index = exportUrl.find(moduleRelativePath)
		if (index < 0):
			return None
		else:
			if archivePath.endswith('/'):
				base = archivePath
			else:
				base = archivePath + "/"

			return base + self.config.tempDir + self.name + "/" + exportUrl[index + len(moduleRelativePath) + 1:]

	def build(self):
		# start build
		print("[%s] build..." % self.name)

		# get diff
		differ = SvnDiffWorker()
		fromUrl = differ.getUrl(self.config.fromUrl, self.relativePath, self.config.fromVer)
		toUrl = differ.getUrl(self.config.toUrl, self.relativePath, self.config.toVer)
		print("[%s] diff from '%s' to '%s'" % (self.name, fromUrl, toUrl))

		filesUrlArr = differ.getChangedFiles(fromUrl, toUrl)
		if (filesUrlArr == None):
			return
		# print("[%s] diff result:" % self.name)

		print("[%s] start export" % self.name)
		exporter = SvnExporter()
		for f in filesUrlArr:

			f = self._geturl(f, self.config.toUrl, self.relativePath)
			path = self._getpath(f, self.relativePath, self.config.archivePath)
			parentFolder = os.path.dirname(path)

			if (not os.path.exists(parentFolder)):
				os.makedirs(parentFolder)
			exporter.export(f, self.config.toVer, path)

	def archive(self):

		dirpath = os.path.join(self.config.archivePath, self.config.tempDir)
		dirpath = os.path.join(dirpath, self.name)

		if (not os.path.exists(dirpath)):
			return None

		#start archive
		print("[%s] archive..." % self.name)

		topath = os.path.join(self.config.archivePath, self.config.buildDir)
		topath = os.path.join(topath, self.name)

		archiver = Archiver()
		archivePath = archiver.archive(dirpath, topath)

		print("archived:" + topath)

		return {
			"filepath" : archivePath,
			"type" : self.name
		}

class HotfixBuilder:

	'''Build hotfix zip files and generate meta info'''
	def __init__(self, configPath):
		with open(configPath) as cfg_file:
			cfg = json.load(cfg_file)
		self.config = BuildConfig(cfg)
		self.config.tempDir = "temp/"
		self.config.buildDir = "build/"

		self.tempDir = os.path.join(self.config.archivePath, self.config.tempDir)
		self.buildDir = os.path.join(self.config.archivePath, self.config.buildDir)


	def createModule(self, moduleJson, buildCfg):
		name = moduleJson["name"]
		relativePath = moduleJson["relativePath"]
		m = HotfixModule(name, relativePath, buildCfg)

		return m

	def build(self):

		os.makedirs(self.config.tempDir)
		os.makedirs(self.config.buildDir)

		buildCfg = self.config

		list = []
		for m in buildCfg.modules:
			module = self.createModule(m, buildCfg)
			module.build()
			arcInfo = module.archive()

			if (arcInfo is not None):
				list.append(arcInfo)

		return list


	def clean(self):
		print("clean...")

		path = self.config.archivePath

		if os.path.exists(self.tempDir):
			shutil.rmtree(self.tempDir)

		if os.path.exists(self.buildDir):
			shutil.rmtree(self.buildDir)

	def report(self, arcInfoList):
		buildDir = self.config.buildDir

		#flist = [ os.path.join(buildDir, f) for f in os.listdir(buildDir) if os.path.isfile(os.path.join(buildDir, f)) ]

		print('------------------------------------------------------')

		r = Reporter()
		for info in arcInfoList:
			r.addfile(info["filepath"], info["type"])

		r.report()
		print('------------------------------------------------------')


def main():

	configPath = 'config.json'

	builder = HotfixBuilder(configPath)
	builder.clean()
	list = builder.build()
	builder.report(list)

if __name__ == '__main__':
	main()