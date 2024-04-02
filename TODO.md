# Rimworld Translation Extraction

## 1. 提取Defs
   1. [x] 所有非Abstract Def的label、description；
   2. [ ] 非Abstract Def不存在label、description时，查询基类Def获取可能的通用label、description（部分完成？）；
   3. [x] comps、stages之类的列表类型内的label、description（HediffDef、ThoughtDef等）（非下标型提取）；
   4. [ ] QuestScriptDef的ruleString、SlateRef等的提取；
## 2. 提取Patches
   1. [x] 提取对1.1做出修改的Patch，以defName.label/description为键值导出原文；
   2. [ ] 提取对1中剩余部分进行修改的Patch，从被修改过后的Def中提取label、description；
## 3. 提取Keyed
   1. [ ] 初步可以考虑仅从原mod提供的文件夹中拷贝；
   2. [ ] 进阶提取需要配合提取dll中字符串常量的程序（参见Rimtrans/Reflection）获取所有使用.Translate()方法的字符串常量
## 4. 提取Strings
   1. [ ] 这一步应该只需要复制粘贴就可以