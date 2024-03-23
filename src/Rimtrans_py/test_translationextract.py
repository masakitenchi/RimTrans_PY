from file import BFS
import os
import lxml
import unittest
from tkinter import filedialog
import TranslationExtractor as TE
import random
import XMLInheritance as XI




class _LoadTest(unittest.TestCase):
	def setUp(self) -> None:
		self.path = filedialog.askdirectory(title='Select Mod Folder')
		self.files = BFS(self.path, ['.xml'])

	def test_BFS(self) -> None:
		self.assertTrue(len(self.files).__gt__(0))
	
	def test_extract(self) -> None:
		print(TE.extract(self.files, ('Def')))
		print(f'loaded {len(self.files)} files')

	def test_extract_parse(self) -> None:
		Defs, Patches, Languages = XI.load_mod(self.path, 'English', '1.4')
		print(TE.extract_tree(Defs))
		pass
	