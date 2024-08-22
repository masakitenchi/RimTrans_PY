import os
import os.path as OP
from lxml import etree as ET
from dataclasses import dataclass, field


latest_stable_major_ver: tuple[int, int] = (1, 4)

major_versions: tuple[str, ...] = ("1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "default")


@dataclass
class Loadfolders:
    path: str
    IfActive: list[str] = field(default_factory=list)
    IfNotActive: list[str] = field(default_factory=list)


class ModLoadFolder:
    def __init__(self, mod_dir: str) -> None:
        """
        :param mod_dir: mod文件夹的绝对路径
        """
        if not OP.isabs(mod_dir):
            raise ValueError("mod_dir must be an absolute path")
        self.mod_dir = mod_dir
        with os.scandir(mod_dir) as it:
            self.loadfolderfile = next(
                (f for f in it if f.is_file() and "loadfolder" in f.name.lower()), None
            )
        self._loadfolders_by_ver: dict[str, list[Loadfolders]] = {}
        if self.loadfolderfile:
            self._parseLoadFolders()
        if "default" not in self._loadfolders_by_ver.keys():
            # Which means loadfolders.xml doesn't have a <default>
            if (
                len(self._loadfolders_by_ver.keys()) == 0
            ):  # No version specific folders (loadfolders.xml doesn't even exist)
                self._generatedefaultLoadFolders()
                for ver in self._loadfolders_by_ver.keys():
                    if ver == "default":
                        continue
                    for folder in self._loadfolders_by_ver["default"]:
                        self._loadfolders_by_ver[ver].append(folder)
            else:
                try:
                    # Find the 'latest' version in loadfolders.xml
                    self._loadfolders_by_ver["default"] = next(
                        self._loadfolders_by_ver[f]
                        for f in major_versions[-2:0:-1]
                        if f in self._loadfolders_by_ver.keys()
                    )
                except StopIteration:
                    # Not sure when this will happen, but it really can happen
                    self._loadfolders_by_ver["default"] = []

    def _generatedefaultLoadFolders(self) -> None:
        self._loadfolders_by_ver["default"] = [Loadfolders(self.mod_dir)]
        for dir in filter(lambda x: os.path.isdir(x), os.scandir(self.mod_dir)):
            if dir.name in major_versions:
                if dir.name not in self._loadfolders_by_ver.keys():
                    self._loadfolders_by_ver[dir.name] = []
                self._loadfolders_by_ver[dir.name].append(
                    Loadfolders(os.path.normpath(os.path.join(self.mod_dir, dir.path)))
                )
            else:
                pass  # Vanilla also has a behaviour that parses through all folders that tries to find a folder matches version string, but I don't want to add it atm
            path = os.path.normpath(f"{self.mod_dir}/Common")
            if os.path.exists(path):
                for ver in self._loadfolders_by_ver.keys():
                    self._loadfolders_by_ver[ver].append(Loadfolders(path))
                    self._loadfolders_by_ver[ver].append(
                        Loadfolders(os.path.normpath(self.mod_dir))
                    )

    def _parseLoadFolders(self) -> None:
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
                if name not in self._loadfolders_by_ver:
                    self._loadfolders_by_ver[name] = []
                for folder in filter(
                    lambda x: type(x) is ET._Element and x.text is not None, node
                ):
                    folder: ET._Element
                    IfModActives: list[str] | None = folder.get("IfModActive", None)
                    if IfModActives is not None:
                        IfModActives = IfModActives.split(",")
                    IfModNotActives: list[str] | None = folder.get(
                        "IfModNotActive", None
                    )
                    if IfModNotActives is not None:
                        IfModNotActives = IfModNotActives.split(",")
                    if folder.text == "/" or folder.text == "\\":
                        self._loadfolders_by_ver[name].append(
                            Loadfolders(
                                os.path.normpath(self.mod_dir),
                                IfModActives,
                                IfModNotActives,
                            )
                        )
                    else:
                        self._loadfolders_by_ver[name].append(
                            Loadfolders(
                                os.path.normpath(
                                    os.path.join(self.mod_dir, folder.text)
                                ),
                                IfModActives,
                                IfModNotActives,
                            )
                        )
            elif name.lower() == "default":
                if "default" not in self._loadfolders_by_ver:
                    self._loadfolders_by_ver["default"] = []
                for folder in filter(
                    lambda x: type(x) is ET._Element and x.text is not None, node
                ):
                    folder: ET._Element
                    IfModActives: list[str] | None = folder.get("IfModActive", None)
                    if IfModActives is not None:
                        IfModActives = IfModActives.split(",")
                    IfModNotActives: list[str] | None = folder.get(
                        "IfModNotActive", None
                    )
                    if IfModNotActives is not None:
                        IfModNotActives = IfModNotActives.split(",")
                    if folder.text == "/" or folder.text == "\\":
                        self._loadfolders_by_ver["default"].append(
                            Loadfolders(
                                os.path.normpath(self.mod_dir),
                                IfModActives,
                                IfModNotActives,
                            )
                        )
                    else:
                        self._loadfolders_by_ver["default"].append(
                            Loadfolders(
                                os.path.normpath(
                                    os.path.join(self.mod_dir, folder.text)
                                ),
                                IfModActives,
                                IfModNotActives,
                            )
                        )

    def __call__(self, ver: str) -> list[Loadfolders]:
        """
        Get the load folders for a specific RimWorld version\n
        ModLoadFolder[ver] is also supported

        :param ver: RimWorld version, in major.minor format
        :returns: list of Loadfolders, if the version doesn't exist, return default loadfolders instead
        """
        if ver not in self._loadfolders_by_ver.keys():
            return self._loadfolders_by_ver["default"]
        return self._loadfolders_by_ver[ver]

    __getitem__ = __call__

    def allSupportedVersions(self) -> list[str]:
        """
        Get all supported RimWorld versions
        """
        return list(f for f in self._loadfolders_by_ver.keys() if f != "default")
