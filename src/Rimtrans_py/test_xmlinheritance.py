from operator import index
import lxml.etree as ET
from Rimtrans_py import file
from XMLInheritance import load_mod_single, load_mods, get_modloadorder, load_mod, XmlInheritanceNode, load_mods_sub
import unittest
from concurrent.futures import ThreadPoolExecutor
import os, random, copy
from tkinter import N, filedialog
from typing import *


class _LoadTest(unittest.TestCase):
	RimWorldFolder = r'D:\SteamLibrary\steamapps\common\RimWorld'
	WorkshopFolder = r'D:\SteamLibrary\steamapps\workshop\content\294100'
	unresolvedNodes: list[XmlInheritanceNode] = []
	resolvedNodes: dict[ET._Element, XmlInheritanceNode] = {}
	nodesByName: dict[str, list[XmlInheritanceNode]] = {}
	def setUp(self) -> None:
		appdata = os.getenv('APPDATA')
		if appdata is not None:
			self.ModsConfigPath = os.path.join(appdata, '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml')
		self.mods = load_mods(RimWorldFolder=self.RimWorldFolder, WorkshopFolder=self.WorkshopFolder)
		self.modLoadOrder = get_modloadorder(self.ModsConfigPath)
	def test_load_parallel(self) -> None:
		for mod in self.modLoadOrder:
			if mod in self.mods.keys():
				cpu_count = os.cpu_count() or 1
				with ThreadPoolExecutor(max_workers=cpu_count // 3) as executor:
					load_mod(self.mods[mod], 'ChineseSimplified', executor=executor)
	def test_load_nonparallel(self) -> None:
		for mod in self.modLoadOrder:
			if mod in self.mods.keys():
				load_mod(self.mods[mod], 'ChineseSimplified')
	def test_write_etree(self) -> None:
		mod = random.choice(list(self.mods.values()))
		print(f'path = "{mod.path}"')
		Defs, Patches, Languages = load_mod(mod, 'ChineseSimplified', '1.4')
		Defs.write('Defs.xml', encoding='utf-8', xml_declaration=True)
		Patches.write('Patches.xml', encoding='utf-8', xml_declaration=True)
		Languages.write('Languages.xml', encoding='utf-8', xml_declaration=True)
	
	def test_load_filedialog(self) -> None:
		mod = load_mod_single(filedialog.askdirectory(title='Select Mod Folder'))
		print(f'path = "{mod.path}"')
		ver = random.choice(mod.supportedversions)
		print(f'supported versions: {mod.supportedversions}, choosing: {ver}')
		Defs, Patches, Languages = load_mod(mod, 'ChineseSimplified', ver)
		Defs.write(os.path.join(mod.path, '..', 'Defs.xml'), encoding='utf-8', xml_declaration=True)
		Patches.write(os.path.join(mod.path, '..', 'Patches.xml'), encoding='utf-8', xml_declaration=True)
		Languages.write(os.path.join(mod.path, '..', 'Languages.xml'), encoding='utf-8', xml_declaration=True)

	def test_resolve_nodes(self) -> None:
		mod = load_mod_single(filedialog.askdirectory(title='Select Mod Folder'))
		print(f'path = "{mod.path}"')
		Defs, Patches, Languages = load_mod(mod, 'ChineseSimplified', '1.4')
		print(f'Loaded {len(list(Defs.getroot()))} nodes')
		for node in list(Defs.getroot()):
			attr_name = node.get('Name')
			attr_parentname = node.get('ParentName')
			if attr_name is None and attr_parentname is None: continue
			if attr_name is not None and self.nodesByName.get(attr_name) is not None:
				for possible_duplicate in self.nodesByName[attr_name]:
					if possible_duplicate.mod == mod:
						if mod is None:
							print(f'Error: node with Name = {attr_name} already exists')
							continue
						print(f'Error: node with Name = {attr_name} already exists in mod {mod.path}')
						continue
			
			self.unresolvedNodes.append(XmlInheritanceNode(node, mod))

			if attr_name is not None:
				if self.nodesByName.get(attr_name) is not None:
					self.nodesByName[attr_name].append(self.unresolvedNodes[-1])
					continue
				self.nodesByName[attr_name] = []
				self.nodesByName[attr_name].append(self.unresolvedNodes[-1])
		self.resolve_parents_and_children()
		self.resolve_nodes()
		print(f'Resolved {len(self.resolvedNodes)} nodes')
		tree = ET.ElementTree(ET.Element('Defs'))
		root = tree.getroot()
		for node in self.resolvedNodes.keys():
			root.append(node)
		Defs.write(os.path.join(mod.path, '..', 'Def_Origin.xml'), encoding='utf-8', xml_declaration=True)
		tree.write(os.path.join(mod.path, '..', 'Def_Unified.xml'), encoding='utf-8', xml_declaration=True)
		


	def resolve_nodes(self):
		for node in filter(lambda x: x.parent is None or x.parent.ResolvedXmlNode is not None, self.unresolvedNodes):
			self.resolve_nodes_recursive(node)
		for node in self.unresolvedNodes:
			if node.ResolvedXmlNode is None:
				print(f'Error: node {node.XmlNode.tag} has not been resolved')
			else:
				self.resolvedNodes[node.XmlNode] = node
		self.unresolvedNodes.clear()

	def resolve_nodes_recursive(self, node: XmlInheritanceNode) -> None:
		if node.ResolvedXmlNode is not None:
			if node.XmlNode.find('defName') is not None:
				text = node.XmlNode.find('defName').text
			else:
				text = f'Name={node.XmlNode.get("Name","")} and ParentName={node.XmlNode.get('ParentName','')}'
			print(f'Warning: {text} has been resolved before, cyclic inheritance')
			return
		self.resolve_node_for(node)
		for child in node.children:
			self.resolve_nodes_recursive(child)

	def resolve_node_for(self, node: XmlInheritanceNode) -> None:
		"""
		Consider only label and description
		"""
		if node.parent is None:
			node.ResolvedXmlNode = node.XmlNode
			return
		if node.parent.ResolvedXmlNode is None:
			print(f'Error: parent node {node.parent.XmlNode.tag} has not been resolved')
			node.ResolvedXmlNode = node.XmlNode
			return
		self.check_duplicate_nodes(node.XmlNode, node.parent.ResolvedXmlNode)
		label = node.XmlNode.find('label')
		if label is None:
			cur = node
			label = ET.Element('label')
			node.XmlNode.append(label)
			parent = cur.parent
			while parent is not None:
				p_label = parent.ResolvedXmlNode.find('label')
				if p_label is not None:
					print(f'Message: {node.XmlNode.find("defName").text if node.XmlNode.find("defName") is not None else node.XmlNode.tag} label resolved to "{p_label.text}"')
					label.text = p_label.text
					break
				cur = parent
				parent = parent.parent
		description = node.XmlNode.find('description')
		if description is None:
			cur = node
			description = ET.Element('description')
			node.XmlNode.append(description)
			parent = cur.parent
			while parent is not None:
				parent = cur.parent
				p_description = parent.ResolvedXmlNode.find('description')
				if p_description is not None:
					print(f'Message: {node.XmlNode.find("defName").text if node.XmlNode.find("defName") is not None else node.XmlNode.tag} label resolved to {p_description.text}')
					description.text = p_description.text
					break
				cur = parent
				parent = parent.parent
		node.ResolvedXmlNode = node.XmlNode

	

	def check_duplicate_nodes(self, node: ET._Element, root: ET._Element) -> None:
		self.usedNames = set()
		for subnode in node.iterchildren():
			if type(subnode) is ET._Element and subnode.find('li') is not None and not self.try_add(self.usedNames, subnode.tag):
				print(f'Error: duplicate node with Name = {subnode.tag}')
		self.usedNames.clear()
		for subnode in node.iterchildren():
			if type(subnode) is ET._Element:
				self.check_duplicate_nodes(subnode, root)


	def resolve_parents_and_children(self):
		for node in self.unresolvedNodes:
			if node.XmlNode.get('ParentName') is not None:
				node.parent = self.get_best_parent_for(node, node.XmlNode.get('ParentName'))
				if node.parent is not None:
					node.parent.children.append(node)

	@staticmethod
	def try_add(set: set, value: Any) -> bool:
		if value in set: return False
		set.add(value)
		return True

	def get_best_parent_for(self, node: XmlInheritanceNode, parent_name: str) -> XmlInheritanceNode | None:
		"""
		Copied vanilla code
		"""
		if self.nodesByName.get(parent_name) is None: 
			print(f'Error: parent node with Name = {parent_name} not found')
			return None
		parents = self.nodesByName[parent_name]
		ans = None
		if node.mod.packageId == '':
			for parent in parents:
				if parent.mod.packageId == '':
					ans = parent
					break
			if ans is None:
				for parent in parents:
					if ans is None or self.modLoadOrder.index(parent.mod.packageId) < self.modLoadOrder.index(ans.mod.packageId):
						ans = parent
		else:
			for parent in parents:
				if parent.mod.packageId != '' and \
					self.modLoadOrder.index(parent.mod.packageId) <= self.modLoadOrder.index(node.mod.packageId) and \
						(ans is None or self.modLoadOrder.index(parent.mod.packageId) > self.modLoadOrder.index(ans.mod.packageId)):
					ans = parent
			if ans is None:
				for parent in parents:
					if parent.mod.packageId == '':
						ans = parent
						break
		if ans is None:
			print(f'Error: parent node with Name = {parent_name} not found')
			return None
		return ans





if __name__ == '__main__':
	unittest.main()
