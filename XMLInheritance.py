import lxml.etree as ET
import os
from file import BFS
from tkinter import filedialog
import platform
from TranslationExtractor import ModLoader as ml
import typing
from dataclasses import dataclass

RimWorldId = 294100
WorkshopFolder: str = ""
RimWorldFolder: str = ""

modLoadOrder: list[str] = []

DefDictByType: dict[str, dict[str, ET._Element]] = {}
"""
Key为DefType，Value为defName:ET._Element的字典
"""
NameAttrDict: dict[str, list[ET._Element]] = {}
"""
key是Name属性，value是拥有该Name属性的节点的列表
"""
expansion_dir = ['Core', 'Royalty', 'Ideology', 'Biotech']

mods: dict[str , str] = {}
"""
packageId:Abspath
"""

@dataclass
class Def:
	sourcepackageId: str
	defName: str
	defType: str
	Element: ET._Element

def load_Def(path: str):
	pass

def load_Patches(path:str):
	pass

def load_Languages(path:str):
	pass


def load_mod(packageId:str, path:str) -> typing.Any:
	modLoader = ml.ModLoadFolder(path)
	for folder in list(modLoader):
		print(folder)

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
		if parentName in NameAttrDict.keys():
			parents = NameAttrDict[parentName]
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

def get_mods():
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

def main():
	global RimWorldFolder, WorkshopFolder, DefDictByType, NameAttrDict, modLoadOrder
	RimWorldFolder = filedialog.askdirectory(title='Choose your RimWorld folder')
	WorkshopFolder = os.path.normpath(os.path.join(RimWorldFolder, f'../../workshop/content/{RimWorldId}'))
	#print(RimWorldFolder)
	#print(WorkshopFolder)
	get_mods()
	#print(mods)
	#load_vanilla(os.path.join(RimWorldFolder, 'Data'))
	#print(os.getenv('APPDATA'))
	if platform.system() == 'Windows':
		if os.path.exists(os.path.normpath(os.path.join(os.getenv('APPDATA'), '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios', 'Config', 'ModsConfig.xml'))):
			_modloadorder(os.path.normpath(os.path.join(os.getenv('APPDATA'), '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios', 'Config', 'ModsConfig.xml')))
		else:
			filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
			_modloadorder(filepath)
	else:
		#TODO: Linux and MacOS
		filepath = filedialog.askopenfilename(title='Choose you ModsConfig.xml', filetypes=[('XML files', '*.xml')])
		_modloadorder(filepath)

	#print(f'Mod count: {len(modLoadOrder)}')
	#print(f'mods: {len(mods)}')
	for mod in modLoadOrder:
		if mod in mods.keys():
			print(f'Loading mod with packageId {mod}: {mod in mods.keys()}')
			load_mod(mod, mods[mod])


if __name__ == "__main__":
	main()