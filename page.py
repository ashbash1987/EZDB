import re

class PageManager(object):
    _pageCollections = {}

    def __init__(self):
        self._pageCollections = {}
        pass
    
    def registerPageCollection(self, pageCollectionClass):            
        self._pageCollections[pageCollectionClass.__name__] = pageCollectionClass
        
    def __getattr__(self, name):
        if name in self._pageCollections:
            return self._pageCollections[name]
        return super(PageManager, self).__getattr__(self, name)   
    
    def __getitem__(self, name):
        if name in self._pageCollections:
            return self._pageCollections[name]
        return super(PageManager, self).__getitem__(self, name)
        
    def resolvePath(self, path):
        for pageCollection in self._pageCollections.values():
            for page in pageManager.PAGES:     
                match = re.search(page[0], path)
                if match is not None:
                    return page[1], match.groups()
        return None, None
            
pages = PageManager()

class PageManagerMetaclass(type):
    """
    A metaclass for pages which will automatically register classes inherting from PageManager. 
    """
    def __new__(cls, name, bases, dct):
        global pages
        classObject = type.__new__(cls, name, bases, dct)
        pages.registerPageCollection(classObject)
        return classObject

class PageCollection(object):
    __metaclass__ = PageManagerMetaclass
    PAGES = [] 
                    