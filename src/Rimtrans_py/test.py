import lxml.etree as ET
import os, random, json, platform
import unittest
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog
from FileParser import BFS
from ModLoadFolder import ModLoadFolder
from ModLoader import load_mod_single, load_mods, get_modloadorder, load_mod
from XmlInheritanceResolver import XMLInheritance as XI

@unittest.skipIf(platform.system() != 'Windows', 'Windows only at the moment')
@unittest.skipIf(not os.path.exists(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'test.json')), 'test.json not found')
class Test(unittest.TestCase):
	def setUp(self) -> None:
		filedir = os.path.split(os.path.abspath(__file__))[0]
		with open(os.path.join(filedir, 'test.json'), 'rb') as config_file:
			config = json.load(config_file)
			if 'RimWorldFolder' in config.keys():
				self.RimWorldFolder = config['RimWorldFolder']
			if 'WorkshopFolder' in config.keys():
				self.WorkshopFolder = config['WorkshopFolder']
			if platform.system() == 'Windows':
				appdata = os.getenv('APPDATA')
				if appdata is not None:
					self.ModsConfigPath = os.path.join(appdata, '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml')
			else:
				self.ModsConfigPath = filedialog.askopenfilename(title='Select ModsConfig.xml')
		args = {
			os.path.join(self.RimWorldFolder, 'Data') : None,
			os.path.join(self.RimWorldFolder, 'Mods') : None,
			self.WorkshopFolder : '_steam'
			}
		self.mods = load_mods(args)
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
	
	def test_core_loadfolder(self) -> None:
		print(ModLoadFolder("D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Data\\Core")._loadfolders)
	
	def test_mod_loadfolder(self) -> None:
		print(ModLoadFolder("D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Mods\\HSK_CN")._loadfolders)

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
		inheritance = XI(self.modLoadOrder)
		inheritance.try_register_all_from(Defs, mod)
		inheritance._resolve_parents_and_children()
		inheritance._resolve_nodes()
		print(f'Resolved {len(inheritance.resolvedNodes)} nodes')
		tree = ET.ElementTree(ET.Element('Defs'))
		root = tree.getroot()
		for node in inheritance.resolvedNodes.keys():
			root.append(node)
		Defs.write(os.path.join(mod.path, '..', 'Def_Origin.xml'), encoding='utf-8', xml_declaration=True)
		tree.write(os.path.join(mod.path, '..', 'Def_Unified.xml'), encoding='utf-8', xml_declaration=True)

	def test_BFS(self) -> None:
		mod = random.choice(list(self.mods.values()))
		files = BFS(mod.path, ['.xml'])
		self.assertTrue(len(files) > 0)
		print(f'Found {len(files)} XML files in {mod.path}')


if __name__ == '__main__':
	unittest.main()
