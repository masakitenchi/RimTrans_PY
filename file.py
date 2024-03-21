import os
import os.path as OP


def BFS(root: str, format: list[str]) -> list[str]:
	"""给定根目录，递归查找所有格式存在于format内的文件

	:param root: 根目录
	:param format: 文件格式，为None时返回所有文件
	:return: 所有文件的绝对路径
	"""
	format = [f.removeprefix('.') for f in format]
	result = []
	for cur, dirs, files in os.walk(root):
		#print(files)
		if format is None:
			for file in files:
				result.append(OP.abspath(OP.join(cur, file)))
		else:
			for file in filter(lambda x: x.split('.')[-1] in format, files):
				result.append(OP.abspath(OP.join(cur, file)))
		for dir in dirs:
			result.extend(BFS(OP.abspath(OP.join(cur, dir)), format))
	return result


def listdir_abspath(path: str, format: list[str]) -> list[str]:
	"""返回path目录下所有格式在format内的文件的绝对路径
	:raise ValueError: if format is None
	"""
	if format is None: raise ValueError('format cannot be None')
	return [os.path.abspath(os.path.join(path, f))
		for f in os.listdir(path)
		if f.split('.')[-1] in format
	]