from typing import Hashable, overload, Any


@overload
def try_add(set: set, value: Any) -> bool: ...
@overload
def try_add(dict: dict, KVpair: tuple[Hashable, Hashable]) -> bool: ...
def try_add(container: Any, value: Any) -> bool:
	"""
	:returns: True if value is added to container, False if value is already in container
	"""
	if container is None: return False
	if type(container) is set:
		if value in container: return False
		container.add(value)
		return True
	if type(container) is dict:
		if value[0] in container.keys(): return False
		container[value[0]] = value[1]
		return True