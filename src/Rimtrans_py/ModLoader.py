import os
import os.path as OP
from lxml import etree as ET


class ModLoadFolder:

    def __init__(self, mod_dir: str, vertuple: tuple = (1, 4)):
        """
        :param mod_dir: mod文件夹的绝对路径
        :param vertuple: RimWorld版本号，默认为1.4，使用tuple(int, int)表示
        """
        if not OP.isabs(mod_dir):
            raise ValueError("mod_dir must be an absolute path")
        self.mod_dir = mod_dir
        self.loadfolderfile = next(
            (f for f in os.scandir(mod_dir) if f.is_file() and "loadfolder" in f.name.lower()), None
        )
        self._loadfolders: set[str] = set()
        if self.loadfolderfile:
            self._parseLoadFolders(vertuple=vertuple)
        else:
            # ModContentPack.cs
            path = os.path.normpath(f'{mod_dir}/{vertuple[0]}.{vertuple[1]}')
            if os.path.exists(path):
                self._loadfolders.add(path)
            else: pass # Vanilla also has this behaviour, but I don't want to add it
            path = os.path.normpath(f'{mod_dir}/Common')
            if os.path.exists(path):
                self._loadfolders.add(path)
            self._loadfolders.add(os.path.normpath(mod_dir))

    def _parseLoadFolders(self, vertuple: tuple = (1, 4)):
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
                if vertuple == tuple(map(int, name.split("."))):
                    for folder in filter(lambda x: type(x) is ET._Element and x.text is not None, node):
                        if folder.text == '/' or folder.text == '\\':
                            self._loadfolders.add(os.path.normpath(self.mod_dir))
                        else:
                            self._loadfolders.add(os.path.normpath(os.path.join(self.mod_dir,folder.text)))
                    return
            elif name.lower() == 'default':
                for folder in filter(lambda x: type(x) is ET._Element and x.text is not None, node):
                        if folder.text == '/' or folder.text == '\\':
                            self._loadfolders.add(self.mod_dir)
                        else:
                            self._loadfolders.add(os.path.normpath(os.path.join(self.mod_dir,folder.text)))
                return
            
    def __iter__(self):
        for folder in self._loadfolders:
            yield folder


if __name__ == "__main__":
    print(ModLoadFolder("D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Mods\\Core_SK_Patch")._loadfolders)
