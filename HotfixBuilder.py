# -*- coding: utf-8 -*-
# @Author: xClouder
# @Date:   2017-08-26 15:13:19
# @Last Modified by:   xClouder
# @Last Modified time: 2017-08-26 18:37:08
import subprocess
import json

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
		return

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

	def build(self):
		# start build
		print("[%s] build..." % self.name)

		# get diff
		differ = SvnDiffWorker()
		fromUrl = differ.getUrl(self.config.fromUrl, self.relativePath, self.config.fromVer)
		toUrl = differ.getUrl(self.config.toUrl, self.relativePath, self.config.toVer)
		print("[%s] diff from '%s' to '%s'" % (self.name, fromUrl, toUrl))

		filesUrlArr = differ.getChangedFiles(fromUrl, toUrl)
		print("[%s] diff result:" % self.name)

		print("[%s] start export" % self.name)
		exporter = SvnExporter()
		for f in filesUrlArr:
			print(f)
			print("toUrl:" + self.config.toUrl)
			path = f.replace(self.config.toUrl, self.config.archivePath)
			
			exporter.export(f, self.config.toVer, path)


		


def createModule(moduleJson, buildCfg):
	name = moduleJson["name"]
	relativePath = moduleJson["relativePath"]
	m = HotfixModule(name, relativePath, buildCfg)

	return m


def main():
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