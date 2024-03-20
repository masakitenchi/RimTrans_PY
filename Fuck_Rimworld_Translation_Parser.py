import os
import os.path
import re
import sys

"""
Rimworld treat all folders in loadfolders.xml as one virtual folder, thus:
Lets say if you have two files with the same name and the same defType, but in different folders:
 - Mod1/Languages/English/DefInjected/ThingDef/ThingDef.xml
 - Mod2/Languages/English/DefInjected/ThingDef/ThingDef.xml
Then congratulations, game will only load the "first" file (which, counter-intuitively, is the last mod listed in LoadFolders.xml), and all translations in the second file is lost.
You may wonder why this could ever happen, but the game treat them as a dict, which, if is written in C#, would be:

Dictionary<string, HashSet<string>> dict = new Dictionary<string, HashSet<string>>();

where the key in dict is the name of the mod, and the value in HashSet has its "Mod1" removed, which would be "Languages/English/DefInjected/ThingDef/ThingDef.xml".
See? So when trying to load the second file, the game will just ignore it since the value is already in the HashSet.

This script, is to rename all files in the Languages folder to the format of "ModName_FileName", to make sure there won't be any "conflict" when loading translations.
"""

mod_name_regex = re.compile(r'.*\\(?P<name>.*)\\Languages.*')

def Fuck_Rimworld_Translation_Parser(rootdir: str):
	for cur, _, files in os.walk(rootdir):
		match = mod_name_regex.match(cur)
		if match:
			print(cur + " name : " + match['name'].replace(' ', '_'))
			for file in files:
				print(f"rename {os.path.join(cur, file)} to {match['name'].replace(' ', '_')}_{file}")
				os.rename(os.path.join(cur, file), os.path.join(cur, match['name'].replace(' ', '_') + '_' + file))



if __name__ == '__main__':
	if os.path.isdir(sys.argv[1]):
		Fuck_Rimworld_Translation_Parser(sys.argv[1])
	else:
		Fuck_Rimworld_Translation_Parser('.')