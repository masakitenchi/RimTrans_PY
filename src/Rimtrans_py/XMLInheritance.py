from json import load
import lxml.etree as ET
import os, platform, time, argparse, random

from regex import F
from file import BFS
from tkinter import NO, filedialog
from ModLoadFolder import ModLoadFolder
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from typing import *


@dataclass
class ModContentPack:
	path: str
	packageId: str
	"""no _steam postfix"""
	loadfolders: ModLoadFolder
	supportedversions: list[str]
	modDependencies: list[str]
	def __init__(self, path: str, packageId: str) -> None:
		self.path = path
		self.packageId = packageId
		self.loadfolders = ModLoadFolder(path)
		self.supportedversions = self.loadfolders.allSupportedVersions()
		self.modDependencies = []
	



@dataclass
class XmlInheritanceNode:
	XmlNode: ET._Element
	mod: ModContentPack
	ResolvedXmlNode: ET._Element = None
	parent: "XmlInheritanceNode" = None
	childrens: list[ET._Element] = field(default_factory=list)

	def is_abstract(self) -> bool:
		return self.XmlNode.get('Abstract').lower() == 'True'


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

unresolvedNodes: dict[str, XmlInheritanceNode] = {}
"""
defName:XmlInheritanceNode
"""
resolvedNodes: set[XmlInheritanceNode] = set()




def split_list(l: list, n: int) -> list[list]:
	k, m = divmod(len(l), n)
	return [l[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]
def Combine(rootTag: str, *args: ET._ElementTree) -> ET._ElementTree:
	root: ET._Element = ET.Element(rootTag)
	tree = ET.ElementTree(root)
	for t in args:
		t: ET._ElementTree
		troot: ET._Element = t.getroot()
		for node in iter(troot):
			root.append(node)
	return tree
def load_xmls(path: str, rootTag: str, executor: ThreadPoolExecutor = None) -> ET._ElementTree:
	
	files = BFS(path, ['.xml'])
	if len(files) == 0: return ET.ElementTree(ET.Element(rootTag))
	if executor is None:
		return load_xmls_sub(files, rootTag)
	tasks: list[Future] = []
	for flist in split_list(files, executor._max_workers):
		future = executor.submit(load_xmls_sub, flist, rootTag)
		tasks.append(future)
	results: list[ET._ElementTree] = [future.result() for future in tasks]
	return Combine(rootTag, *results)

def load_xmls_sub(paths: list[str], rootTag: str) -> ET._ElementTree:
	root = ET.Element(rootTag)
	tree = ET.ElementTree(root)
	for path in paths:
		try:
			f: ET._ElementTree = ET.parse(path)
			froot: ET._Element = f.getroot()
			if froot.tag != rootTag:
				raise ValueError(f'root node is {froot.tag}, expected {rootTag}')
			for node in filter(lambda x: type(x) is ET._Element, froot):
				node.set('Path', path)
				root.append(node)
		except Exception as e:
			print(f'Error when parsing file {path} : {e}')
			continue
	return tree

def load_mod(mod: ModContentPack, language: str = '', version: str = '1.4', executor: Optional[ThreadPoolExecutor] = None) -> tuple[ET._ElementTree, ET._ElementTree, ET._ElementTree]:
	"""
	Given a path to a mod's folder, \nload all XMLs in loadfolders/(Defs, Patches, [Languages]), combine them into different ElementTrees
	:param path: path to the mod's folder
	:param language: language to load, leave it None to skip loading
	:param executor: ThreadPoolExecutor to use, leave it None to use single thread
	:return: a tuple of ET._ElementTree containing XML tree of Defs, Patches, and Languages
	"""
	modLoader = ModLoadFolder(mod.path)
	result: list[ET._ElementTree] = [ET.ElementTree(ET.Element('Defs')), ET.ElementTree(ET.Element('Patches')), ET.ElementTree(ET.Element('LanguageData'))]
	for folder in modLoader[version]:
		result[0] = Combine('Defs', *(result[0], load_xmls(os.path.join(folder.path, 'Defs'), 'Defs', executor=executor)))
		result[1] = Combine('Patch', *(result[1], load_xmls(os.path.join(folder.path, 'Patches'), 'Patch', executor=executor)))
		if language != '' and os.path.exists(os.path.join(folder.path, 'Languages')):
			try:
				LanguageDataFolder = next(os.path.join(folder.path, 'Languages', f) for f in os.listdir(os.path.join(folder.path, 'Languages')) if (os.path.isdir(os.path.join(folder.path, 'Languages', f)) and language in f))
				result[2] = Combine('LanguageData', *(result[2], load_xmls(LanguageDataFolder, 'LanguageData', executor=executor)))
			except StopIteration:
				continue
	return tuple(result)


def get_modloadorder(path: str) -> list[str]:
	modLoadOrder = []
	if path is None:
		path = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
	tree: ET._ElementTree = ET.parse(path)
	root: ET._Element = tree.getroot()
	for mod in list(root.find('activeMods')):
		modLoadOrder.append(mod.text)
	return modLoadOrder

def load_mods(RimWorldFolder: str, WorkshopFolder: str) -> dict[str, ModContentPack]:
	mods = {}
	if RimWorldFolder is None or WorkshopFolder is None: return dict()
	mods.update(load_mods_sub(os.path.join(RimWorldFolder, 'Data')))
	mods.update(load_mods_sub(os.path.join(RimWorldFolder, 'Mods')))
	mods.update(load_mods_sub(WorkshopFolder, '_steam'))
	return mods

def load_mods_sub(path: str, idPostfix: Optional[Literal['_steam']] = None) -> dict[str, ModContentPack]:
	mods = {}
	for entry in filter(lambda x: x.is_dir(), os.scandir(path)):
		mod = load_mod_single(entry.path, idPostfix)
		if mod.packageId != '':
			mods[mod.packageId] = mod
		else:
			print(f'Warning: mod in "{entry.path}" has no packageId')
	return mods

def load_mod_single(path: str, idPostfix: Optional[Literal['_steam']] = None) -> ModContentPack:
	if os.path.exists(os.path.join(path, 'About', 'About.xml')):
		tree: ET._ElementTree = ET.parse(os.path.join(path, 'About', 'About.xml'))
		root: ET._Element = tree.getroot()
		if root.find('packageId') is None: 
			print(f'Warning: "{os.path.join(path, "About", "About.xml")}" has no packageId')
			return ModContentPack(path, '')
		packageId = root.find('packageId').text.lower()
		if idPostfix is not None: packageId += idPostfix
		return ModContentPack(path, packageId)
	print(f'Warning: "{os.path.join(path, "About", "About.xml")}" not found')
	return ModContentPack(path, '')

def main(parallel: bool = False, activeLanguage: str = 'ChineseSimplified') -> None:
	global RimWorldFolder, WorkshopFolder, DefsByDefType, ElementsByAttrName
	RimWorldFolder = filedialog.askdirectory(title='Choose your RimWorld folder')
	WorkshopFolder = os.path.normpath(os.path.join(RimWorldFolder, f'../../workshop/content/{RimWorldId}'))
	if not os.path.exists(RimWorldFolder):
		print('RimWorld folder not found')
		return
	mods = load_mods(RimWorldFolder=RimWorldFolder, WorkshopFolder=WorkshopFolder)
	if platform.system() == 'Windows':
		if os.path.exists(os.path.normpath(os.path.join(os.getenv('APPDATA'), '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios', 'Config', 'ModsConfig.xml'))):
			print('Using default ModsConfig.xml?(Y/N)')
			if input().lower() == 'y':
				modLoadOrder = get_modloadorder(os.path.normpath(os.path.join(os.getenv('APPDATA'), '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios', 'Config', 'ModsConfig.xml')))
			else:
				filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
				modLoadOrder = get_modloadorder(filepath)
		else:
			filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
			modLoadOrder = get_modloadorder(filepath)
	else:
		#TODO: Linux and MacOS
		filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
		modLoadOrder = get_modloadorder(filepath)
	if parallel:
		ttstart = time.time()
		for mod in modLoadOrder:
			if mod in mods.keys():
				with ThreadPoolExecutor(max_workers=os.cpu_count() // 3) as executor:
					load_mod(mods[mod], activeLanguage, executor=executor)
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