# -*- coding: utf-8 -*-
# @Author: xClouder
# @Date:   2017-08-26 15:13:19
# @Last Modified by:   xClouder
# @Last Modified time: 2017-08-28 18:56:53
import subprocess
import json
import os

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
			raise Exception("diff failed" + output)

		filearr = output.split()
		return filearr

class SvnExporter:
	'''Export changed files to workspace'''
	def export(self, fileUrl, ver, toPath):
		print("export:" + toPath)
		verStr = ""
		if (ver != None):
			verStr = "-r" + str(ver)

		exportCmd = "svn export %s -q --force %s %s" % (verStr, fileUrl, toPath)
		print("execute shell:" + exportCmd)
		p = subprocess.Popen(exportCmd, stdout=subprocess.PIPE, shell=True)
		(output, err) = p.communicate()

class Archiver:
	def archive(self, folder, toFile):
		return


class Reporter:
	def filesize(fname):
		return os.path.getsize(fname)

	def md5(fname):
		hash_md5 = hashlib.md5()
		with open(fname, "rb") as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash_md5.update(chunk)
		return hash_md5.hexdigest()

	def report(self, file):
		print("report:" + file)
		print("file md5:" + md5(file))
		print("file size:" + str(filesize(file)))



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

			return base + self.name + "/" + exportUrl[index + len(moduleRelativePath) + 1:]



	def build(self):
		# start build
		print("[%s] build..." % self.name)

		# get diff
		differ = SvnDiffWorker()
		fromUrl = differ.getUrl(self.config.fromUrl, self.relativePath, self.config.fromVer)
		toUrl = differ.getUrl(self.config.toUrl, self.relativePath, self.config.toVer)
		print("[%s] diff from '%s' to '%s'" % (self.name, fromUrl, toUrl))

		filesUrlArr = differ.getChangedFiles(fromUrl, toUrl)
		# for f in filesUrlArr:


		print("[%s] diff result:" % self.name)

		print("[%s] start export" % self.name)
		exporter = SvnExporter()
		for f in filesUrlArr:

			f = self._geturl(f, self.config.toUrl, self.relativePath)
			path = self._getpath(f, self.relativePath, self.config.archivePath)
			parentFolder = os.path.dirname(path)

			if (not os.path.exists(parentFolder)):
				os.makedirs(parentFolder)
			exporter.export(f, self.config.toVer, path)


def createModule(moduleJson, buildCfg):
	name = moduleJson["name"]
	relativePath = moduleJson["relativePath"]
	m = HotfixModule(name, relativePath, buildCfg)

	return m


def main():

	# diffedUrl = "svn://172.16.1.9/ezfun/xgame2/client/trunk/Assets/StreamingAssets/Lua/LuaModule/windowmgr.lua"
	# reltivePath = "Assets/StreamingAssets/Lua"
	# newTargetUrl = "svn://172.16.1.9/ezfun/xgame2/client/branchs/20170818/XGame2"

	# m = HotfixModule("Lua", "aa", None)
	# ret = m._geturl(diffedUrl, newTargetUrl, reltivePath)
	# print(ret)
	# return

	with open('config.json') as cfg_file:
		cfg = json.load(cfg_file)

	buildCfg = BuildConfig(cfg)

	for m in cfg["modules"]:
		module = createModule(m, buildCfg)
		module.build()


	# dw = SvnDiffWorker()
	# files = dw.getChangedFiles(oldUrl, newUrl)
	# for f in files:
	# 	print(f)

if __name__ == '__main__':
	main()