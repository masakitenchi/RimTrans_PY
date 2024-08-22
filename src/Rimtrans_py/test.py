import lxml.etree as ET
import os, random, json, platform
import unittest
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog
from fileparser import BFS
from ModLoadFolder import ModLoadFolder
from ModLoader import (
    load_mod,
    generate_mod_dict,
    get_modloadorder,
    load_mod,
    load_mod_single,
)
from TranslationExtractor import extract_single_def, extract_tree, key_list, format_list
from XmlInheritanceResolver import XMLInheritance as XI


@unittest.skipIf(platform.system() != "Windows", "Windows only at the moment")
@unittest.skipIf(
    not os.path.exists(
        os.path.join(os.path.split(os.path.abspath(__file__))[0], "test.json")
    ),
    "test.json not found",
)
class Test(unittest.TestCase):
    def setUp(self) -> None:
        filedir = os.path.split(os.path.abspath(__file__))[0]
        with open(os.path.join(filedir, "test.json"), "rb") as config_file:
            config = json.load(config_file)
            if "RimWorldFolder" in config.keys():
                self.RimWorldFolder = config["RimWorldFolder"]
            if "WorkshopFolder" in config.keys():
                self.WorkshopFolder = config["WorkshopFolder"]
            if platform.system() == "Windows":
                appdata = os.getenv("APPDATA")
                if appdata is not None:
                    self.ModsConfigPath = os.path.join(
                        appdata,
                        "../LocalLow/Ludeon Studios/RimWorld by Ludeon Studios/Config/ModsConfig.xml",
                    )
            else:
                self.ModsConfigPath = filedialog.askopenfilename(
                    title="Select ModsConfig.xml"
                )
        args = {
            os.path.join(self.RimWorldFolder, "Data"): None,
            os.path.join(self.RimWorldFolder, "Mods"): None,
            self.WorkshopFolder: "_steam",
        }
        self.mods = generate_mod_dict(args)
        self.modLoadOrder = get_modloadorder(self.ModsConfigPath)

    def test_load_parallel(self) -> None:
        for mod in self.modLoadOrder:
            if mod in self.mods.keys():
                cpu_count = os.cpu_count() or 1
                with ThreadPoolExecutor(max_workers=cpu_count // 3) as executor:
                    load_mod(self.mods[mod], "ChineseSimplified", executor=executor)

    def test_load_nonparallel(self) -> None:
        for mod in self.modLoadOrder:
            if mod in self.mods.keys():
                load_mod(self.mods[mod], "ChineseSimplified")

    def test_write_etree(self) -> None:
        mod = random.choice(list(self.mods.values()))
        print(f'path = "{mod.path}"')
        Defs, Patches, Languages = load_mod(mod, "ChineseSimplified", "1.4")
        Defs.write("Defs.xml", encoding="utf-8", xml_declaration=True)
        Patches.write("Patches.xml", encoding="utf-8", xml_declaration=True)
        Languages.write("Languages.xml", encoding="utf-8", xml_declaration=True)

    def test_core_loadfolder(self) -> None:
        print(
            ModLoadFolder(
                "D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Data\\Core"
            )._loadfolders_by_ver
        )

    def test_mod_loadfolder(self) -> None:
        print(
            ModLoadFolder(
                "D:\\SteamLibrary\\steamapps\\common\\RimWorld\\Mods\\HSK_CN"
            )._loadfolders_by_ver
        )

    @unittest.skip("no reason")
    def test_load_filedialog(self) -> None:
        mod = load_mod_single(filedialog.askdirectory(title="Select Mod Folder"))
        print(f'path = "{mod.path}"')
        ver = random.choice(mod.supportedversions)
        print(f"supported versions: {mod.supportedversions}, choosing: {ver}")
        Defs, Patches, Languages = load_mod(mod, "ChineseSimplified", ver)
        Defs.write(
            os.path.join(mod.path, "..", "Defs.xml"),
            encoding="utf-8",
            xml_declaration=True,
        )
        Patches.write(
            os.path.join(mod.path, "..", "Patches.xml"),
            encoding="utf-8",
            xml_declaration=True,
        )
        Languages.write(
            os.path.join(mod.path, "..", "Languages.xml"),
            encoding="utf-8",
            xml_declaration=True,
        )

    def test_resolve_nodes(self) -> None:
        mod = load_mod_single(os.path.join(self.RimWorldFolder, "Data", "Core"))
        print(f'path = "{mod.path}"')
        Defs, Patches, Languages = load_mod(mod, "ChineseSimplified", "1.4")
        inheritance = XI(self.modLoadOrder)
        inheritance.try_register_all_from(Defs, mod)
        inheritance.start_resolve()
        tree = ET.ElementTree(ET.Element("Defs"))
        root = tree.getroot()
        for node in inheritance.resolvedNodes.keys():
            root.append(node)

    def test_BFS(self) -> None:
        mod = random.choice(list(self.mods.values()))
        files = BFS(mod.path, [".xml"])
        self.assertTrue(len(files) > 0)
        print(f"Found {len(files)} XML files in {mod.path}")

    def test_resolve(self) -> None:
        mod = load_mod_single(os.path.join(self.RimWorldFolder, "Data", "Core"))
        Defs, _, _ = load_mod(mod, "ChineseSimplified", "1.4")
        result_before = set(extract_tree(Defs))
        print(f"Before resolving: {len(result_before)} nodes")
        inheritance = XI(self.modLoadOrder)
        inheritance.try_register_all_from(Defs, mod)
        inheritance.start_resolve()
        result_after = set(extract_tree(Defs))
        for item in filter(lambda x: x[1], result_after - result_before):
            print(item)
        print(f"After resolving: {len(result_after)} nodes")

    def test_key_list(self) -> None:
        string = "<stages>	  <li>		<label>shivering</label>		<becomeVisible>false</becomeVisible>	  </li>	  <li>		<label>shivering</label>		<minSeverity>0.04</minSeverity>		<capMods>		  <li>			<capacity>Manipulation</capacity>			<offset>-0.08</offset>		  </li>		  <li>			<capacity>Consciousness</capacity>			<offset>-0.05</offset>		  </li>		</capMods>	  </li>	  <li>		<label>minor</label>		<minSeverity>0.2</minSeverity>		<capMods>		  <li>			<capacity>Moving</capacity>			<offset>-0.1</offset>		  </li>		  <li>			<capacity>Manipulation</capacity>			<offset>-0.2</offset>		  </li>		  <li>			<capacity>Consciousness</capacity>			<offset>-0.10</offset>		  </li>		</capMods>	  </li>	  <li>		<label>serious</label>		<minSeverity>0.35</minSeverity>		<painOffset>0.15</painOffset>		<capMods>		  <li>			<capacity>Moving</capacity>			<offset>-0.3</offset>		  </li>		  <li>			<capacity>Manipulation</capacity>			<offset>-0.5</offset>		  </li>		  <li>			<capacity>Consciousness</capacity>			<offset>-0.20</offset>		  </li>		</capMods>	  </li>	  <li>		<label>extreme</label>		<minSeverity>0.62</minSeverity>		<lifeThreatening>true</lifeThreatening>		<painOffset>0.30</painOffset>		<capMods>		  <li>			<capacity>Consciousness</capacity>			<setMax>0.1</setMax>		  </li>		</capMods>	  </li>	</stages>"
        node = ET.fromstring(string)
        self.assertEqual(key_list(node), ['shivering-0', 'shivering-1', 'minor', 'serious', 'extreme'])
        string = """
        <stages>
            <li>
                <label>trivial</label>
                <socialFightChanceFactor>1.5</socialFightChanceFactor>
                <hungerRateFactorOffset>0.5</hungerRateFactorOffset>
                <capMods>
                <li>
                    <capacity>Consciousness</capacity>
                    <offset>-0.05</offset>
                </li>
                </capMods>
            </li>
            <li>
                <minSeverity>0.2</minSeverity>
                <label>minor</label>
                <socialFightChanceFactor>2</socialFightChanceFactor>
                <hungerRateFactorOffset>0.6</hungerRateFactorOffset>
                <capMods>
                <li>
                    <capacity>Consciousness</capacity>
                    <offset>-0.10</offset>
                </li>
                </capMods>
            </li>
            <li>
                <minSeverity>0.4</minSeverity>
                <label>moderate</label>
                <socialFightChanceFactor>2.5</socialFightChanceFactor>
                <hungerRateFactorOffset>0.6</hungerRateFactorOffset>
                <capMods>
                <li>
                    <capacity>Consciousness</capacity>
                    <offset>-0.20</offset>
                </li>
                </capMods>
            </li>
            <li>
                <minSeverity>0.6</minSeverity>
                <label>severe</label>
                <socialFightChanceFactor>3</socialFightChanceFactor>
                <hungerRateFactorOffset>0.6</hungerRateFactorOffset>
                <capMods>
                <li>
                    <capacity>Consciousness</capacity>
                    <offset>-0.30</offset>
                </li>
                </capMods>
            </li>
            <li>
                <minSeverity>0.8</minSeverity>
                <label>extreme</label>
                <lifeThreatening>true</lifeThreatening>
                <hungerRateFactorOffset>0.6</hungerRateFactorOffset>
                <capMods>
                <li>
                    <capacity>Consciousness</capacity>
                    <setMax>0.1</setMax>
                </li>
                </capMods>
            </li>
        </stages>
        """
        node = ET.fromstring(string)
        self.assertEqual(key_list(node), ['trivial', 'minor', 'moderate', 'severe', 'extreme'])

    def test_format_list(self) -> None:
        string = """
        <stages>
            <li>
                <label>tainted {0}</label>
                <description>I am wearing a piece of apparel that someone died in. It creeps me out and feels dirty.</description>
                <baseMoodEffect>-5</baseMoodEffect>
            </li>
            <li>
                <label>tainted {0} (+1)</label>
                <description>I am wearing two pieces of apparel that someone died in. It creeps me out and feels dirty.</description>
                <baseMoodEffect>-8</baseMoodEffect>
            </li>
            <li>
                <label>tainted {0} (+2)</label>
                <description>I am wearing three pieces of apparel that someone died in. It creeps me out and feels dirty.</description>
                <baseMoodEffect>-11</baseMoodEffect>
            </li>
            <li>
                <label>tainted {0} etc</label>
                <description>I am wearing four or more pieces of apparel that someone died in. It creeps me out and feels dirty.</description>
                <baseMoodEffect>-14</baseMoodEffect>
            </li>
        </stages>
        """
        node = ET.fromstring(string)
        self.assertEqual(format_list(node), ['tainted', 'tainted_1', 'tainted_2', 'tainted_etc'])


    def test_extract_Def(self) -> None:
        string = """<TraitDef>
    <defName>Nudist</defName>
    <commonality>0.7</commonality>
    <degreeDatas>
      <li>
        <label>nudist</label>
        <description>{PAWN_nameDef} enjoys the feeling of freedom that comes from being nude. {PAWN_pronoun} can handle clothing, but will be happier without it.</description>
      </li>
    </degreeDatas>
  </TraitDef>"""
        node = ET.fromstring(string)
        result = extract_single_def(node)
        print(result)


if __name__ == "__main__":
    unittest.main()
