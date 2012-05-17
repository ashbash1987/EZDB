class EZDBEntityManager(object):
    _entityClasses = {}

    def __init__(self):
        self._entityClasses = {}
        pass
    
    def registerEntityClass(self, entityClass):            
        self._entityClasses(entityClass.__name__) = entityClass
        
    def __getattr__(self, name):
        if name in self._entityClasses:
            return self._entityClasses[name]
        return super(EZDBEntityManager, self).__getattr__(self, name)   
    
    def __getitem__(self, name):
        if name in self._entityClasses:
            return self._entityClasses[name]
        return super(EZDBEntityManager, self).__getitem__(self, name)           

entities = EZDBEntityManager()