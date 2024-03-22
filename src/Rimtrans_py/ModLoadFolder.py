import os
import os.path as OP
from lxml import etree as ET
from dataclasses import dataclass
import unittest



latest_stable_major_ver: tuple[int,int] = (1,4)

major_versions: set[str] = {'1.0', '1.1', '1.2', '1.3', '1.4', '1.5', 'default'}

@dataclass
class Loadfolders:
    path: str
    IfActive: list[str]
    IfNotActive: list[str]

class ModLoadFolder:
    def __init__(self, mod_dir: str):
        """
        :param mod_dir: mod文件夹的绝对路径
        """
        if not OP.isabs(mod_dir):
            raise ValueError("mod_dir must be an absolute path")
        self.mod_dir = mod_dir
        self.loadfolderfile = next(
            (f for f in os.scandir(mod_dir) if f.is_file() and "loadfolder" in f.name.lower()), None
        )
        self._loadfolders: dict[str, list[Loadfolders]] = {ver: [] for ver in major_versions}
        if self.loadfolderfile:
            self._parseLoadFolders()
        else:
            # ModContentPack.cs
            print(f'Warning :: mod in {mod_dir} doesn\'t have loadfolders.xml, reading root dir instead')
            for dir in filter(lambda x: os.path.isdir(x), os.scandir(mod_dir)):
                if dir.name in major_versions:
                    self._loadfolders[dir.name].append(Loadfolders(os.path.normpath(os.path.join(mod_dir, dir.path))))
                else: pass # Vanilla also has this behaviour, but I don't want to add it
                path = os.path.normpath(f'{mod_dir}/Common')
                if os.path.exists(path):
                    for ver in self._loadfolders.keys():
                        self._loadfolders[ver].append(Loadfolders(path))
                        self._loadfolders[ver].append(Loadfolders(os.path.normpath(mod_dir)))
    def _parseLoadFolders(self):
        # Vanilla Behaviour:
        tree = ET.parse(f"{self.mod_dir}/{self.loadfolderfile.name}")
        root: ET._Element = tree.getroot()
        if "loadfolder" not in root.tag.lower():
            raise ValueError(
                f"Error when parsing loadfolders in {self.mod_dir}: expected root tag 'loadfolder', got {root.tag} "
            )
        for node in filter(lambda x: type(x) is ET._Element, root):
            name: str = node.tag.lower()
            if "v" in name:
                name = name[1:]
                for folder in filter(lambda x: type(x) is ET._Element and x.text is not None, node):
                    folder: ET._Element
                    IfModActives: list[str] | None = folder.get('IfModActive', None)
                    if IfModActives is not None: IfModActives = IfModActives.split(',')
                    IfModNotActives: list[str] | None = folder.get('IfModNotActive', None)
                    if IfModNotActives is not None: IfModNotActives = IfModNotActives.split(',')
                    if folder.text == '/' or folder.text == '\\':
                        self._loadfolders[name].append(Loadfolders(
                                                        os.path.normpath(self.mod_dir),
                                                        IfModActives,
                                                        IfModNotActives))
                    else:
                        self._loadfolders[name].append(Loadfolders(
                                                        os.path.normpath(os.path.join(self.mod_dir,folder.text)),
                                                        IfModActives,
                                                        IfModNotActives))
            elif name.lower() == 'default':
                for folder in filter(lambda x: type(x) is ET._Element and x.text is not None, node):
                        folder: ET._Element
                        IfModActives: list[str] | None = folder.get('IfModActive', None)
                        if IfModActives is not None: IfModActives = IfModActives.split(',')
                        IfModNotActives: list[str] | None = folder.get('IfModNotActive', None)
                        if IfModNotActives is not None: IfModNotActives = IfModNotActives.split(',')
                        if folder.text == '/' or folder.text == '\\':
                            self._loadfolders['default'].append(Loadfolders(
                                                            os.path.normpath(self.mod_dir),
                                                            IfModActives,
                                                            IfModNotActives))
                        else:
                            self._loadfolders['default'].append(Loadfolders(
                                                            os.path.normpath(os.path.join(self.mod_dir,folder.text)),
                                                            IfModActives,
                                                            IfModNotActives))
    def __call__(self, ver: str) -> list[Loadfolders]:
        """
        Get the load folders for a specific RimWorld version
        ModLoadFolder[ver] is also supported

        :param ver: RimWorld version, in major.minor format
        """
        return self._loadfolders[ver]
    
    __getitem__ = __call__


class ModLoadFolderTest(unittest.TestCase):
    def test_core(self):
        ModLoadFolder("D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Data\\Core")._loadfolders
    
    def test_mod(self):
        ModLoadFolder("D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Mods\\HSK_CN")._loadfolders

""" if __name__ == "__main__":
    unittest.main() """
