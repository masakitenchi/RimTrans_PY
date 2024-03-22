import unittest
from ModLoadFolder import ModLoadFolder

class _ModLoadFolderTest(unittest.TestCase):
    def test_core(self):
        print(ModLoadFolder("D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Data\\Core")._loadfolders)
    
    def test_mod(self):
        print(ModLoadFolder("D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Mods\\HSK_CN")._loadfolders)

if __name__ == '__main__':
    unittest.main()