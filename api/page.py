import re

global _pathManagers

class PageManagerMetaclass(type):
    """
    A metaclass for pages which will automatically register classes inherting from PageManager. 
    """
    def __new__(cls, name, bases, dct):
        global _pathManagers
        classObject = type.__new__(cls, name, bases, dct)
        _pathManagers.append(classObject)                    
        return classObject

class PageManager(object):
    __metaclass__ = PageManagerMetaclass
    __pages__ = []
        
def resolvePath(path):
    global _pathManagers
    for pathManager in _pathManagers:
        for page in pathManager.__pages__:
            match = re.search(page[0], path)
            if match is not None:
                return page[1], match.groups()
    return None, None    
                    