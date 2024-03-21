import lxml.etree as ET
import os
from file import BFS
from tkinter import filedialog
import platform
from TranslationExtractor import ModLoader as ml
import typing
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
import time
import argparse

RimWorldId = 294100
WorkshopFolder: str = ""
RimWorldFolder: str = ""

modLoadOrder: list[str] = []

DefsByDefType: dict[str, dict[str, ET._Element]] = {}
"""
Key为DefType，Value为defName:ET._Element的字典
"""
ElementsByAttrName: dict[str, list[ET._Element]] = {}
"""
key是Name属性，value是拥有该Name属性的节点的列表
"""
expansion_dir = ['Core', 'Royalty', 'Ideology', 'Biotech']

mods: dict[str , str] = {}
"""
packageId:Abspath
"""


@dataclass
class XmlInheritanceNode:
	XmlNode: ET._Element
	ResolvedXmlNode: ET._Element
	mod: str
	parent: ET._Element
	childrens: list[ET._Element] = field(default_factory=list)

def split_list(l: list, n: int) -> list[list]:
	k, m = divmod(len(l), n)
	return [l[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]

def load_xmls(path: str, rootTag: str, executor: ThreadPoolExecutor = None) -> ET._ElementTree:
	def Combine(trees: list[ET._ElementTree], rootTag: str) -> ET._ElementTree:
		root = ET.Element(rootTag)
		tree = ET.ElementTree(root)
		for t in trees:
			t: ET._ElementTree
			troot: ET._Element = t.getroot()
			for node in troot:
				root.append(node)
		return tree
	files = BFS(path, ['.xml'])
	if len(files) == 0: return None
	if executor is None:
		return load_xmls_sub(files, rootTag)
	tasks: list[Future] = []
	for flist in split_list(files, os.cpu_count() // 3):
		future = executor.submit(load_xmls_sub, flist, rootTag)
		tasks.append(future)
	results = [future.result() for future in tasks]
	return Combine(results, rootTag)

def load_xmls_sub(paths: list[str], rootTag: str) -> ET._ElementTree:
	root = ET.Element(rootTag)
	tree = ET.ElementTree(root)
	for path in paths:
		try:
			f: ET._ElementTree = ET.parse(path)
			f: ET._ElementTree
			froot: ET._Element = f.getroot()
			if froot.tag != rootTag:
				raise ValueError(f'root node is {froot.tag}, expected {rootTag}')
			for node in filter(lambda x: type(x) is ET._Element, froot):
				root.append(node)
		except Exception as e:
			print(f'Error when parsing file {path} : {e}')
			continue
	return tree

def load_mod(path:str, language: str, executor: ThreadPoolExecutor = None) -> list[ET._ElementTree, ET._ElementTree, ET._ElementTree]:
	modLoader = ml.ModLoadFolder(path)
	result: list[ET._ElementTree, ET._ElementTree, ET._ElementTree] = []
	for folder in list(modLoader):
		result.append(load_xmls(os.path.join(folder, 'Defs'), 'Defs', executor=executor))
		result.append(load_xmls(os.path.join(folder, 'Patches'), 'Patch', executor=executor))
		if os.path.exists(os.path.join(folder, 'Languages')):
			try:
				LanguageDataFolder = next(f for f in os.listdir(os.path.join(folder, 'Languages')) if os.path.isdir(f) and language in f)
				result.append(load_xmls(LanguageDataFolder, 'LanguageData', executor=executor))
			except StopIteration:
				continue
	return result


def _modloadorder(path: str):
	global modLoadOrder
	if path is None:
		path = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
	tree: ET._ElementTree = ET.parse(path)
	root: ET._Element = tree.getroot()
	for mod in list(root.find('activeMods')):
		modLoadOrder.append(mod.text)

def find_best_inheritance_node(node: ET._Element) -> ET._Element:
	"""
	查找最佳的继承节点
	Args:
		node: ET._Element : 要查找继承节点的节点
	Returns:
		ET._Element: 最佳的继承节点，None when node has no ParentName or not found
	"""
	defName = node.find('defName').text
	defType = node.tag
	possible_parents = []
	if node.get('parentName', None) is not None:
		parentName = node.get('parentName')
		if parentName in ElementsByAttrName.keys():
			parents = ElementsByAttrName[parentName]
			for parent in parents:
				#当然只会考虑相同类型的Def
				if parent.tag == node.tag:
					possible_parents.append(parent)
		else:
			raise ValueError(f'节点{node.tag}.{defName}的parentName属性值{parentName}不存在')
	else:
		return None
	#TODO: 读取用户的modsConfig.xml以获取mod加载顺序以获取最后一个加载的对应Def
	return possible_parents.pop()

def _get_mods():
	global mods
	for cur, dirs, _ in os.walk(os.path.join(RimWorldFolder, 'Mods')):
		# Local mods
		for dir in dirs:
			if os.path.exists(os.path.join(cur, dir, 'About', 'About.xml')):
				tree: ET._ElementTree = ET.parse(os.path.join(cur, dir, 'About', 'About.xml'))
				root: ET._Element = tree.getroot()
				if root.find('packageId') is None: 
					print(f'Error: {os.path.join(cur, dir, "About", "About.xml")} has no packageId')
					continue
				packageId: str = root.find('packageId').text.lower()
				mods[packageId] = os.path.join(cur, dir)
		break
		
	for cur, dirs, _ in os.walk(WorkshopFolder):
		# Workshop mods
		for dir in dirs:
			if os.path.exists(os.path.join(cur, dir, 'About', 'About.xml')):
				tree: ET._ElementTree = ET.parse(os.path.join(cur, dir, 'About', 'About.xml'))
				root: ET._Element = tree.getroot()
				if root.find('packageId') is None: 
					print(f'Error: {os.path.join(cur, dir, "About", "About.xml")} has no packageId')
					continue
				packageId: str = (root.find('packageId').text + '_steam').lower()
				mods[packageId] = os.path.join(cur, dir)
		break
				
	for cur, dirs, _ in os.walk(os.path.join(RimWorldFolder, 'Data')):
		# Vanilla
		for dir in dirs:
			if os.path.exists(os.path.join(cur, dir, 'About', 'About.xml')):
				tree: ET._ElementTree = ET.parse(os.path.join(cur, dir, 'About', 'About.xml'))
				root: ET._Element = tree.getroot()
				if root.find('packageId') is None: 
					print(f'Error: {os.path.join(cur, dir, "About", "About.xml")} has no packageId')
					continue
				packageId : str = root.find('packageId').text.lower()
				mods[packageId] = os.path.join(cur, dir)
		break

def main(parallel: bool = False, activeLanguage: str = 'ChineseSimplified'):
	global RimWorldFolder, WorkshopFolder, DefsByDefType, ElementsByAttrName, modLoadOrder
	RimWorldFolder = filedialog.askdirectory(title='Choose your RimWorld folder')
	WorkshopFolder = os.path.normpath(os.path.join(RimWorldFolder, f'../../workshop/content/{RimWorldId}'))
	if not os.path.exists(RimWorldFolder):
		print('RimWorld folder not found')
		return
	_get_mods()
	if platform.system() == 'Windows':
		if os.path.exists(os.path.normpath(os.path.join(os.getenv('APPDATA'), '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios', 'Config', 'ModsConfig.xml'))):
			print('Using default ModsConfig.xml?(Y/N)')
			if input().lower() == 'y':
				_modloadorder(os.path.normpath(os.path.join(os.getenv('APPDATA'), '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios', 'Config', 'ModsConfig.xml')))
			else:
				filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
				_modloadorder(filepath)
		else:
			filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
			_modloadorder(filepath)
	else:
		#TODO: Linux and MacOS
		filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
		_modloadorder(filepath)
	if parallel:
		ttstart = time.time()
		for mod in modLoadOrder:
			if mod in mods.keys():
				with ThreadPoolExecutor(max_workers=os.cpu_count() // 3) as executor:
					load_mod(mods[mod], activeLanguage, executor)
		ttend = time.time()
		print(f'Loaded all mods in {(ttend - ttstart) * 1000:.2f} ms (parallel)')
	else:
		ttstart = time.time()
		for mod in modLoadOrder:
			if mod in mods.keys():
				load_mod(mods[mod], activeLanguage)
		ttend = time.time()
		print(f'Loaded all mods in {(ttend - ttstart) * 1000:.2f} ms (nonparallel)')



if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Load mods and parse XMLs')
	parser.add_argument('--parallel', action='store_true', help='Use parallel loading')
	args = parser.parse_args()
	if args.parallel:
		main(True)
	else:
		main()