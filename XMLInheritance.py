import lxml.etree as ET
import os
import random
from file import BFS



DefDictByType: dict[str, dict[str, ET._Element]] = {}
"""
Key为DefType，Value为defName:ET._Element的字典
"""
NameAttrDict: dict[str, list[ET._Element]] = {}
"""
key是Name属性，value是拥有该Name属性的节点的列表
"""
expansion_dir = ['Core', 'Royalty', 'Ideology', 'Biotech']

def load_vanilla(path: str) -> dict[str, dict[str, ET._Element]]:
	"""
	加载原版xml文件
	
	Args:
		path (str): 原版Data文件夹的路径
	Returns:
		dict[str, dict[str, ET._Element]]: 完整的字典，按照DefType.defName的方式存储
	"""
	global DefDictByType, NameAttrDict
	for dir in (f for f in os.listdir(path) if f in expansion_dir):
		Defs = os.path.join(path, dir, 'Defs')
		print(Defs)
		files = BFS(Defs, ['xml'])
		print(files)
		for file in files:
			try:
				tree: ET._ElementTree = ET.parse(file)
				root: ET._Element = tree.getroot()
				if root.tag != 'Defs': raise ValueError(f'File has no root tag named "Defs"')
				for node in list(root):
					node: ET._Element
					defName = ""
					if type(node) is ET._Comment: continue
					if node.tag not in DefDictByType.keys():
						DefDictByType[node.tag] = {}
					if node.get('Abstract', '').lower() == 'true':
						continue
					if node.find('defName') is not None:	defName = node.find('defName').text
					else: raise ValueError(f'Node in file named {node.tag} has no defName, while it\'s not an abstract node. (Abstract attribute is not True)')
					""" if defName in DefDictByType[node.tag].keys().keys():
						raise ValueError(f'文件 {file} 的节点{node.tag}的defName重复') """
					DefDictByType[node.tag][defName] = node
					attr = node.get('Name', None)
					if attr is not None:
						if attr not in NameAttrDict.keys():
							NameAttrDict[attr] = []
						NameAttrDict[attr].append(node)
			except Exception as e:
				print(f'Error when loading file {file} : node.defName= {defName}\n message: {e}')
				continue
	return DefDictByType


def find_best_inheritance_node(node: ET._Element):
	"""
	查找最佳的继承节点
	
	Args:
		node (ET._Element): 要查找继承节点的节点
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



if __name__ == "__main__":
	load_vanilla(r'D:\SteamLibrary\steamapps\common\RimWorld\Data')
	print(DefDictByType.keys())
	print(f'Done. Parsed {len(DefDictByType.keys())} files.')
	root = ET.Element('Defs')
	tree = ET.ElementTree(root)
	for DefType, Defs in DefDictByType.items():
		for defName, node in Defs.items():
			root.append(node)
	tree.write('Defs.xml', pretty_print=True, xml_declaration=True, encoding='utf-8')
