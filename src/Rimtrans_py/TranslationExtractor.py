import os
import os.path
import lxml.etree as ET
import regex as re
import argparse
import typing
from file import BFS

"""
Consider using ElephantTusk.tools.point.label instead of ElephantTusk.tools.1.label for translation '尖' (Items_Exotic.xml)

where 'point' is the text of label, '1' is the index of the item in the list
"""

# Find all patches that target defs with defName
xpath_regex = re.compile(
    r"Defs\/(?<defType>.*?Def)\[(?<defNames>.*)\]\/(?<field>label|description)"
)

defNames_regex = re.compile(r'defName\W*?=\W*?"(?<defName>.*?)"')


Defs_xpath = ET.XPath("//*[preceding-sibling::defName or following-sibling::defName][self::label or self::description]/..")

Patch_xpath = '//xpath[contains(text(),"label") or contains(text(),"description") and not(contains(text(), "labelShort"))]/..'

#lxml seems doesn't support local-name()
Anomaly_xpath = '//*[@Class="PatchOperationAdd"]/xpath[text()="Defs"]/../value/*[not(@Abstract) or (@Abstract!="True" and @Abstract!="true")]'

def extract_sub(tree: ET._ElementTree, xpath: str, targets: list[str]) -> typing.Any:
    """
    :param root: The parsed xml tree for extraction
    :param xpath:
    """
    nodes: list[ET._Element] = tree.xpath(xpath)
    for node in nodes:
        for subelement in node.iter():
            if type(subelement) == ET._Element:
                if subelement.tag != 'li':
                    print(subelement.tag + ' ' + subelement.text if subelement.text is not None else '')
                else:
                    print('li ' + subelement.get('Class', ''))



def extract(list_paths: list[str], target=('Def', 'Patch')) -> dict[str, dict[str, str]]:
    """
    总提取函数
    :param list_paths: 所有文件的绝对路径列表
    :param target: 提取目标，Def或Patch
    :return: dict[defType: str, dict[defName: str, field: str]] 按defType分类的提取结果
    """
    pairs: dict[str, dict[str, str]] = dict()
    for file in list_paths:
        try:
            count = 0
            if not os.path.isabs(file) or not os.path.isfile(file):
                raise Exception(f"path {file} does not target a file or is not absolute")
            tree = ET.parse(file)
            root: ET._Element = tree.getroot()
            if root.tag == "Defs" and 'Def' in target:
                # only looks for non-virtual defs
                nodes = Defs_xpath(root)
                for node in nodes:
                    defType = node.tag
                    if defType not in pairs:
                        pairs[defType] = dict()
                    key = node.find("./defName").text
                    pairs[defType][f"{key}.label"] = (
                        node.find("./label").text
                        if node.find("./label") is not None
                        else None
                    )
                    pairs[defType][f"{key}.description"] = (
                        node.find("./description").text
                        if node.find("./description") is not None
                        else None
                    )
            elif root.tag == 'Patch' and 'Patch' in target:
                # looks for all patches that targeting label or description
                nodes = root.xpath(Patch_xpath)
                for node in nodes:
                    xpath = node.find("./xpath")
                    match = re.match(xpath_regex, xpath.text)
                    if match:
                        defType, defName, field = match.groups()
                    else:
                        continue
                    value = node.find(f"./value/{field}").text
                    if defType not in pairs:
                        pairs[defType] = dict()
                    defNames = re.findall(defNames_regex, defName)
                    # print(defNames)
                    for defName in defNames:
                        key = f"{defName}.{field}"
                        pairs[defType][key] = value
                anomaly_nodes = root.xpath(Anomaly_xpath)
                for node in anomaly_nodes:
                    defName = node.find("./defName").text
                    label = node.find("./label").text if node.find("./label") is not None else ""
                    description = node.find("./description").text if node.find("./description") is not None else ""
                    defType = node.tag
                    if defType not in pairs:
                        pairs[defType] = dict()
                    pairs[defType][f"{defName}.label"] = label
                    pairs[defType][f"{defName}.description"] = description
            
        except Exception as e:
            if node is not None:
                print(f"Error when parsing {file}, {node.tag} message: {e}")
            else:
             print(f"Error when parsing {file}, message: {e}")
            continue
    return pairs


def main(dirpath: str, recursive: bool = False) -> dict[str, ET._ElementTree]:
    if not os.path.isdir(dirpath) or not os.path.isabs(dirpath):
        raise Exception("Path is not a dir or absolute path")
    trees = dict()
    if recursive:
        list_files = BFS(dirpath)
    else:
        list_files = [os.path.abspath(f) for f in os.listdir(dirpath) if f.endswith(".xml")]
    # print(list_files)
    pairs = extract(list_files)
    # print(pairs)
    # os.makedirs('extracted', exist_ok=True)
    for defType, results in pairs.items():
        # os.makedirs(f'extracted/{defType}', exist_ok=True)
        root: ET._Element = ET.Element("LanguageData")
        root.addprevious(ET.Comment("This file was generated by Patch_Extract.py"))
        tree: ET._ElementTree = ET.ElementTree(root)
        for key, value in results.items():
            defName = ET.SubElement(root, key)
            defName.text = value
        trees[defType] = tree
    return trees


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", "-f", action="store", metavar="目标文件夹")
    parser.add_argument("--dry-run", '-d', action='store_true', default=True, help='不生成文件，只输出结果')
    result = parser.parse_args()
    if not result.folder:
        path = os.path.abspath(".")
    else:
        path = os.path.abspath(result.folder)
    list_files = BFS(path, ['.xml'])
    print(list_files)
    for file in list_files:
        root = ET.parse(file).getroot()
        if root.tag == 'Defs':
            extract_sub(ET.parse(file), Defs_xpath.path, ['label', 'description'])
    pairs = extract(list_files)
    print(pairs)
    if not result.dry_run:
        os.makedirs("extracted", exist_ok=True)
        for defType, results in pairs.items():
            os.makedirs(f"extracted/{defType}", exist_ok=True)
            root: ET._Element = ET.Element("LanguageData")
            root.addprevious(ET.Comment("This file was generated by Patch_Extract.py"))
            tree: ET._ElementTree = ET.ElementTree(root)
            for key, value in results.items():
                defName = ET.SubElement(root, key)
                defName.text = value
            tree.write(
                f"extracted/{defType}/ExtractedPatch.xml",
                pretty_print=True,
                xml_declaration=True,
                encoding="utf-8",
            )