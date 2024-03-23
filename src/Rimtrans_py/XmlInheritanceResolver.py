from ast import mod
import lxml.etree as ET
from ModLoader import ModContentPack, XmlInheritanceNode
from typing import Any, overload
from utilities import try_add

class XMLInheritance:
	unresolvedNodes: list[XmlInheritanceNode]
	resolvedNodes: dict[ET._Element, XmlInheritanceNode]
	nodesByName: dict[str, list[XmlInheritanceNode]]

	@overload
	def __init__(self, modLoadOrder: list[str]) -> None: ...
	@overload
	def __init__(self, old: "XMLInheritance") -> None: ...
	def __init__(self, arg: Any) -> None:
		"""
		Keep resolvedNodes, nodesByName & modLoadOrder\n
		unresolvedNodes are cleared after resolving
		"""
		if type(arg) is list:
			self.unresolvedNodes = []
			self.resolvedNodes = {}
			self.nodesByName = {}
			self.modLoadOrder = arg
		else:
			arg: XMLInheritance
			self.unresolvedNodes = arg.unresolvedNodes
			self.resolvedNodes = arg.resolvedNodes
			self.nodesByName = arg.nodesByName
			self.modLoadOrder = arg.modLoadOrder


	def try_register_all_from(self, tree: ET._ElementTree, mod: ModContentPack) -> None:
		for node in list(tree.getroot()):
			self._try_register(node, mod)

	def _try_register(self, node: ET._Element, mod: ModContentPack) -> None:
		attr_name = node.get('Name')
		attr_parentname = node.get('ParentName')
		if attr_name is None and attr_parentname is None: return
		if attr_name is not None and self.nodesByName.get(attr_name) is not None:
			for possible_duplicate in self.nodesByName[attr_name]:
				if possible_duplicate.mod == mod:
					if mod is None:
						print(f'Error: node with Name = {attr_name} already exists')
						continue
					print(f'Error: node with Name = {attr_name} already exists in mod {mod.path}')
					continue
		
		XInode = XmlInheritanceNode(node, mod)
		self.unresolvedNodes.append(XInode)

		if attr_name is not None:
			if self.nodesByName.get(attr_name) is not None:
				self.nodesByName[attr_name].append(XInode)
				return
			self.nodesByName[attr_name] = []
			self.nodesByName[attr_name].append(XInode)

	def _resolve_nodes(self) -> None:
		for node in list(filter(
			lambda x: x.parent is None or x.parent.ResolvedXmlNode is not None, 
			self.unresolvedNodes)): # Must not be an enmuerator
			self._resolve_nodes_recursive(node)
		for node in self.unresolvedNodes:
			if node.ResolvedXmlNode is None:
				print(f'Error: node {node.XmlNode.tag} has not been resolved')
			else:
				self.resolvedNodes[node.XmlNode] = node
		self.unresolvedNodes.clear()

	def _resolve_nodes_recursive(self, node: XmlInheritanceNode) -> None:
		if node.ResolvedXmlNode is not None:
			if node.XmlNode.find('defName') is not None:
				text = node.XmlNode.find('defName').text
			else:
				text = f'Name={node.XmlNode.get("Name","")} and ParentName={node.XmlNode.get('ParentName','')}'
			print(f'Warning: {text} has been resolved before, cyclic inheritance')
			return
		self._resolve_node_for(node)
		for child in node.children:
			self._resolve_nodes_recursive(child)

	def _resolve_node_for(self, node: XmlInheritanceNode) -> None:
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
		self._check_duplicate_nodes(node.XmlNode, node.parent.ResolvedXmlNode)
		label = node.XmlNode.find('label')
		if label is None:
			cur = node
			label = ET.Element('label')
			node.XmlNode.append(label)
			parent = cur.parent
			while parent is not None:
				p_label = parent.ResolvedXmlNode.find('label')
				if p_label is not None and p_label.text is not None:
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
				if p_description is not None and p_description.text is not None:
					print(f'Message: {node.XmlNode.find("defName").text if node.XmlNode.find("defName") is not None else node.XmlNode.tag} description resolved to {p_description.text}')
					description.text = p_description.text
					break
				cur = parent
				parent = parent.parent
		node.ResolvedXmlNode = node.XmlNode

	def _check_duplicate_nodes(self, node: ET._Element, root: ET._Element) -> None:
		self.usedNames = set()
		for subnode in node.iterchildren():
			if type(subnode) is ET._Element and subnode.find('li') is not None and not try_add(self.usedNames, subnode.tag):
				print(f'Error: duplicate node with Name = {subnode.tag}')
		self.usedNames.clear()
		for subnode in node.iterchildren():
			if type(subnode) is ET._Element:
				self._check_duplicate_nodes(subnode, root)


	def _resolve_parents_and_children(self) -> None:
		for node in self.unresolvedNodes:
			if node.XmlNode.get('ParentName') is not None:
				node.parent = self._get_best_parent_for(node, node.XmlNode.get('ParentName'))
				if node.parent is not None:
					node.parent.children.append(node)
		return

	def _get_best_parent_for(self, node: XmlInheritanceNode, parent_name: str) -> XmlInheritanceNode | None:
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
