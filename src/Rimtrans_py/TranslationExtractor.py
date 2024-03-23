import os
import os.path
import lxml.etree as ET
import regex as re
import argparse
from typing import *
from Rimtrans_py.FileParser import BFS

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

list_translatable = ['stages', 'lifeStages', 'tools', 'degreeDatas']

class_name_as_key = ['comps']

tag_translatable = ['label', 'labelNoun', 'description', 'jobString']

parameter_regex = re.compile(r'\s?{\d}\s?')
thought_degree_regex = re.compile(r'\s?\(\+(?<degree>\d)\)\s?')

def extract_list(tree: ET._Element) -> list[str]:
    """
    Given an element contains translatable list, return the list of all extracted keys
    :param tree: the element containing the list
    :return: list of keys
    """
    if tree.tag not in list_translatable: return
    keys = []
    index = 0
    for node in tree.iterchildren('li'):
        if node.find('./label') is not None:
            label = node.find('./label').text
            if parameter_regex.search(label) is not None:
                label = parameter_regex.sub('', label) # Remove all " {0} " from the label
            if thought_degree_regex.search(label) is not None:
                degree = thought_degree_regex.search(label)['degree']
                label = thought_degree_regex.sub('', label) + f'_{degree}'
            keys.append(build_key(node, 'label', label=label, index=index))
            if node.find('./description') is not None:
                keys.append(build_key(node, 'description', label=label, index=index))
        index += 1
    return keys


def build_key(node: ET._Element, finalTag: str, *, label: Optional[str] = None, index: int) -> str:
    key = node.find(f'./{finalTag}').text if label is None else label
    if len(key.split(' ')) > 1: #Contains whitespace
        key = key.replace(' ', '_')
    parent = node
    key_str = '.'.join([key, finalTag])
    while True:
        parent = parent.getparent()
        key_str = '.'.join([parent.tag, key_str])
        if parent.find('./defName') is not None:
            key_str = key_str.replace(parent.tag, parent.find('./defName').text)
            break
    return key_str

def extract_single(element: ET._Element) -> list:
    """
    :param element: element
    :returns: a list of keys
    """
    keys = []
    if element.get('Abstract') and element.get('Abstract').lower() == 'true' or element.find('./defName') is None:
        return []
    for node in element.iterchildren():
        if node.tag in list_translatable:
            keys.extend(extract_list(node))
        elif node.tag in tag_translatable:
            keys.append(f"{element.find('./defName').text}.{node.tag}")
    return keys

def extract_tree(tree: ET._ElementTree) -> list:
    root = tree.getroot()
    keys = []
    for node in root.iterchildren():
        keys.extend(extract_single(node))
    return keys


def extract(list_paths: list[str], target: set[Literal['Def', 'Patch']]) -> dict[str, dict[str, str]]:
    """
    总提取函数
    :param list_paths: 所有文件的绝对路径列表
    :param target: 提取目标，Def或Patch
    :return: dict[defType: str, dict[defName: str, field: str]] Similar to DefDataBase<T>, where T is the outer key in this dict
    """
    pairs: dict[str, dict[str, str]] = dict()
    for file in list_paths:
        try:
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