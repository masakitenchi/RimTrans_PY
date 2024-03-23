from XMLInheritance import _get_mods, _modloadorder, load_mod
import unittest
from concurrent.futures import ThreadPoolExecutor
import os
import random



class _LoadTest(unittest.TestCase):
	RimWorldFolder = r'D:\SteamLibrary\steamapps\common\RimWorld'
	WorkshopFolder = r'D:\SteamLibrary\steamapps\workshop\content\294100'
	def setUp(self) -> None:
		appdata = os.getenv('APPDATA')
		if appdata is not None:
			self.ModsConfigPath = os.path.join(appdata, '../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml')
		self.mods = _get_mods(RimWorldFolder=self.RimWorldFolder, WorkshopFolder=self.WorkshopFolder)
		self.modLoadOrder = _modloadorder(self.ModsConfigPath)
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
		#print(self.mods)
		path = str(random.choice(list(self.mods.values())))
		print(f'path = "{path}"')
		Defs, Patches, Languages = load_mod(path, 'ChineseSimplified', '1.4')
		Defs.getroot().text = '\n\t'
		Defs.write('Defs.xml', encoding='utf-8', xml_declaration=True)
		Patches.write('Patches.xml', encoding='utf-8', xml_declaration=True)
		Languages.write('Languages.xml', encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
	unittest.main()
