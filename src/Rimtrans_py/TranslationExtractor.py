from operator import concat
import os
import os.path
import lxml.etree as ET
import regex as re
import argparse
from typing import *
from fileparser import BFS
from utilities import try_add

"""
Consider using ElephantTusk.tools.point.label instead of ElephantTusk.tools.1.label for translation '尖' (Items_Exotic.xml)

where 'point' is the text of label, '1' is the index of the item in the list
"""


xpath_regex = re.compile(
    r"Defs\/(?<defType>.*?Def)\[(?<defNames>.*)\]\/(?<field>label|description)"
)
"""
Find all patches that target certain def\n
Example: Defs/ThingDef[defName="XXX"]/label \n 
-> re.match()['defType'] = 'ThingDef' \n 
-> re.match()['defNames'] = 'defName="XXX"' \n 
-> re.match()['field'] = 'label'
"""

defNames_regex = re.compile(r'defName\W*?=\W*?"(?<defName>.*?)"')
"""
We only consider a patch valid if it targets a non-abstract def for now
"""


Defs_xpath = ET.XPath(
    "//*[preceding-sibling::defName or following-sibling::defName][self::label or self::description]/.."
)

patch_xpath = '//xpath[contains(text(),"label") or contains(text(),"description") and not(contains(text(), "labelShort"))]/..'

# lxml seems doesn't support local-name()
anomaly_xpath = '//*[@Class="PatchOperationAdd"]/xpath[text()="Defs"]/../value/*[not(@Abstract) or (@Abstract!="True" and @Abstract!="true")]'
anomaly_xpath_2 = '//*[@Class="PatchOperationAdd"]/xpath[text()="Defs" or text()="/Defs" or text()="Defs/" or text()="/Defs/"]/../value/*[not(@Abstract) or (@Abstract!="True" and @Abstract!="true")]'

list_translatable = ["stages", "lifeStages", "tools", "degreeDatas"]

class_name_as_key = ["comps"]

tag_translatable = ["label", "labelNoun", "description", "jobString", "labelShort"]

parameter_regex = re.compile(r"\s?{\d}") 
"""{0} {1} {2} ..."""

degree_regex = re.compile(r"\s?\(\+(?<degree>\d)\)\s?") 
"""(+1) (+2) ..."""

def has_sharing_label(listroot: ET._Element) -> bool:
    labels = set()
    count = 0
    for node in listroot.iterchildren("li"):
        if node.find("./label") is not None:
            labels.add(node.find("./label").text)
            count += 1
    return len(labels) != count

def has_format_string(listroot: ET._Element) -> bool:
    for node in listroot.iterchildren("li"):
        if node.find("./label") is not None:
            if parameter_regex.search(node.find("./label").text) is not None:
                return True
    return False

def key_list(listroot: ET._Element) -> list[str]:
    labels = dict()
    result = []
    for node in listroot.iterchildren("li"):
        if node.find("./label") is not None:
            label = node.find("./label").text
            if label in labels:
                labels[label] += 1
            else:
                labels[label] = 0
            result.append(f'{label}-{labels[label]}')
        else: result.append("") # Keep the index
    for res in result:
        if res != "" and labels[res[0:-2]] == 0:
            result[result.index(res)] = res[0:-2]
    return result

def format_list(listroot: ET._Element) -> list[str]:
    result = []
    for node in listroot.iterchildren("li"):
        if node.find("./label") is not None:
            label = node.find("./label").text
            if parameter_regex.search(label) is not None:
                label = parameter_regex.sub("", label)
            if degree_regex.search(label) is not None:
                degree = degree_regex.search(label)["degree"]
                label = degree_regex.sub(" ", label) + f"{degree}"
            label = label.replace(" ", "_")
            result.append(label)
    return result


def extract_list(tree: ET._Element) -> list[tuple[str, str]]:
    """
    Given an element contains translatable list, return the list of all extracted keys
    :param tree: the element containing the list
    :return: list of keys
    """
    keys: list[tuple] = []
    index = 0
    for node in tree.iterchildren("li"):
        if node.find("./label") is not None:
            label = node.find("./label").text
            if has_sharing_label(tree):
                label = key_list(tree)[index]
            elif has_format_string(tree):
                label = format_list(tree)[index]
            keys.append(
                (
                    build_key(node, "label", label=label, index=index),
                    node.find("./label").text,
                )
            )
            if node.find("./description") is not None:
                keys.append(
                    (
                        build_key(node, "description", label=label, index=index),
                        node.find("./description").text,
                    )
                )
        index += 1
    return keys

def build_key(
    node: ET._Element, finalTag: str, *, label: Optional[str] = None, index: int
) -> str:
    key = node.find(f"./{finalTag}").text if label is None else label
    if len(key.split(" ")) > 1:  # Contains whitespace
        key = key.replace(" ", "_")
    if '\'' in key:
        key = key.replace("'", "")
    parent = node
    key_str = ".".join([key, finalTag])
    while True:
        parent = parent.getparent()
        key_str = ".".join([parent.tag, key_str])
        if parent.find("./defName") is not None:
            key_str = key_str.replace(parent.tag, parent.find("./defName").text)
            break
    return key_str


def extract_single_def(element: ET._Element) -> dict[str, dict[str, str]]:
    """
    :param element: element
    """
    if (
        element.get("Abstract")
        and element.get("Abstract").lower() == "true"
        or element.find("./defName") is None
    ):
        return {}
    result = {}
    for node in element.iterchildren():
        if node.tag in list_translatable:
            result.update(extract_list(node))
        elif node.tag in tag_translatable:
            result.update(
                    {f"{element.find('./defName').text}.{node.tag}":
                    node.text}
            )
    return {element.tag: result}

def extract_single_patch(node: ET._Element) -> dict[str, dict[str, str]]:
    """
    :param node: patch xml element
    """
    if node is None: return {}
    patches = node.xpath(patch_xpath)
    anomaly_patches = node.xpath(anomaly_xpath)
    result = {}
    for patch in patches:
        patch: ET._Element
        xpath = patch.find("./xpath")
        match = re.match(xpath_regex, xpath.text)
        if match:
            defType, defName, field = match.groups()
        else:
            continue
        value = patch.find(f"./value/{field}").text
        if defType not in result:
            result[defType] = dict()
        defNames = re.findall(defNames_regex, defName)
        for defName in defNames:
            key = f"{defName}.{field}"
            result[defType][key] = value
    for anomaly in anomaly_patches:
        defName = anomaly.find("./defName").text
        label = (
            anomaly.find("./label").text
            if anomaly.find("./label") is not None
            else ""
        )
        description = (
            anomaly.find("./description").text
            if anomaly.find("./description") is not None
            else ""
        )
        defType = anomaly.tag
        if defType not in result:
            result[defType] = dict()
        result[defType][f"{defName}.label"] = label
        result[defType][f"{defName}.description"] = description
    return result

def extract_tree(tree: ET._ElementTree) -> dict[str, dict[str, str]]:
    """
    Given a xml tree, returns a dict of {defType : {key: value}}
    """
    root = tree.getroot()
    keys: dict[str, dict[str, str]] = {}
    if root.tag == 'Defs':
        func = extract_single_def
        nodeiter = root.iterchildren()
    elif root.tag == 'Patch':
        func = extract_single_patch
        nodeiter = root.xpath(patch_xpath) + root.xpath(anomaly_xpath)
    else:
        return {}
    for node in nodeiter:
        result = func(node)
        for res in result:
            if res not in keys:
                keys[res] = {}
            for key, value in result[res].items():
                if key in keys[res]:
                    keys[res][key] += value
                else:
                    keys[res][key] = value
    return keys


def extract(
    list_paths: list[str], target: set[Literal["Def", "Patch"]]
) -> dict[str, dict[str, str]]:
    """
    总提取函数
    :param list_paths: 所有文件的绝对路径列表
    :param target: 提取目标，Def或Patch
    :return: dict[defType: str, dict[key: str, value: str]] Similar to DefDataBase<T>, where T is the outer key in this dict
    """
    pairs: dict[str, dict[str, str]] = dict()
    for file in list_paths:
        try:
            if not os.path.isabs(file) or not os.path.isfile(file):
                raise Exception(
                    f"path {file} does not target a file or is not absolute"
                )
            tree = ET.parse(file)
            #root: ET._Element = tree.getroot()
            if tree.getroot().tag == "Defs" and "Def" in target:
                # only looks for non-virtual defs
                pairs = extract_tree(tree)
            elif tree.getroot().tag == "Patch" and "Patch" in target:
                # looks for all patches that targeting label or description
                pairs = extract_tree(tree)
        except Exception as e:
            """ 
            if node is not None:
                print(f"Error when parsing {file}, {node.tag} message: {e}")
            else: """
            print(f"Error when parsing {file}, message: {e}")
            continue
    return pairs


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", "-f", action="store", metavar="目标文件夹")
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        default=True,
        help="不生成文件，只输出结果",
    )
    result = parser.parse_args()
    if not result.folder:
        path = os.path.abspath(".")
    else:
        path = os.path.abspath(result.folder)
    list_files = BFS(path, [".xml"])
    print(list_files)
