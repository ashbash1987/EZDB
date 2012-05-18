import copy
import structs
import interface
import view

"""
Enum defining the different flags for an entity.
"""
EntityFlags = structs.enum(NEW=1, DIRTY=2, DELETED=4, CLOSED=8)

class EntityManager(object):
    _entityClasses = {}

    def __init__(self):
        self._entityClasses = {}
        pass
    
    def registerEntityClass(self, entityClass):            
        self._entityClasses[entityClass.__name__] = entityClass
        
    def __getattr__(self, name):
        if name in self._entityClasses:
            return self._entityClasses[name]
        return super(EntityManager, self).__getattr__(self, name)   
    
    def __getitem__(self, name):
        if name in self._entityClasses:
            return self._entityClasses[name]
        return super(EntityManager, self).__getitem__(self, name)           

entities = EntityManager()

class EntityMetaclass(type):
    """
    A metaclass for entities which will automatically populate FIELDS with additional fields given the reference definitions set in REFERENCES.
    """
    def __new__(cls, name, bases, dct):
        global entities
        if "FIELDS" in dct and "REFERENCES" in dct and len("REFERENCES") > 0:
            for k,v in dct["REFERENCES"].items():
                for primaryKey in v.referenceType.PRIMARY:
                    field = copy.deepcopy(v.referenceType.FIELDS[primaryKey])
                    field.attributes = filter(lambda x: x != structs.Attributes.AUTOINCREMENT, field.attributes)
                    dct["FIELDS"][primaryKey] = field
        dct["_ENTITIES"] = {}
        classObject = type.__new__(cls, name, bases, dct)
        entities.registerEntityClass(classObject)
        return classObject
        
    def __call__(cls, *a, **kwargs):
        obj = super(EntityMetaclass, cls).__call__(*a, **kwargs)
        return cls._getFromLocalCache(obj)    
        
class Entity(object):
    """
    Base class for entities that interact directly with the global database.
    """
    __metaclass__ = EntityMetaclass
    
    TABLE = None
    PRIMARY = ()
    UNIQUE = ()
    FIELDS = ()
    REFERENCES = {}
    VIEWS = {}
    
    _ENTITIES = {}
    _INSERT_CALLBACKS = []
    _CHANGE_CALLBACKS = []
    _UPDATE_CALLBACKS = []
    _DELETE_CALLBACKS = []

    @classmethod
    def _getFromLocalCache(cls, obj):
        """
        Method to do local cache resolution, returning an existing entity with an identical uniqueID, or the passed-in obj if there are no matches. 
        """
        uniqueID = obj.uniqueID
        if len(uniqueID) == 0:
            return obj
        if cls._ENTITIES is None:
            cls._ENTITIES = {uniqueID: obj}
            return obj
        if uniqueID not in cls._ENTITIES:
            cls._ENTITIES[uniqueID] = obj
            return obj
        return cls._ENTITIES[uniqueID]        
        
    @classmethod
    def _removeFromLocalCache(cls, obj):
        """
        Removed the object from the local cache according to its uniqueID, if it is set.
        """
        uniqueID = obj.uniqueID
        if len(uniqueID) == 0 or cls._ENTITIES is None or uniqueID not in cls._ENTITIES:
            return
        del cls._ENTITIES[uniqueID]                    
            
    def __init__(self, db, **kwargs):
        """
        Initializer.
        """
        super(Entity, self).__setattr__('_data', {})
        super(Entity, self).__setattr__('_values', {})
        super(Entity, self).__setattr__('_referenceValues', {})
        super(Entity, self).__setattr__('_flags', EntityFlags.NEW)
        super(Entity, self).__setattr__('_insertCallbacks', [])
        super(Entity, self).__setattr__('_changeCallbacks', [])
        super(Entity, self).__setattr__('_updateCallbacks', [])
        super(Entity, self).__setattr__('_deleteCallbacks', [])
        super(Entity, self).__setattr__('_db', db)
        for k,v in kwargs.items():
            self._setValue(k, v)            
        for key in self.PRIMARY:
            if key not in kwargs:
                return                   
        self._isNew = False         
    
    def _onInsert(self):
        """
        Invoked when the entity has been inserted into the database.
        """
        self._isNew = False
        for callback in self._insertCallbacks:
            callback(self)
        self._onInsertType(self)
        Entity._onInsertType(self)
    
    @classmethod
    def _onInsertType(cls, obj):
        """
        Invoked when an entity of 'cls' type has been inserted into the database.
        """
        for callback in cls._INSERT_CALLBACKS:
            callback(obj)                    
    
    def _onChange(self, values):
        """
        Invoked when the entity has been changed locally.
        """
        if not self.isNew():
            self._flags = self._flags | EntityFlags.DIRTY
            for callback in self._changeCallbacks:
                callback(self, values)
            self._onChangeType(self, values)            
            Entity._onChangeType(self, values)
    
    @classmethod
    def _onChangeType(cls, obj, values):
        """
        Invoked when an entity of 'cls' type has been changed locally.
        """
        for callback in cls._CHANGE_CALLBACKS:
            callback(obj, values)

    def _onUpdate(self):
        """
        Invoked when the entity has been updated in the database.
        """
        self._flags = self._flags & (~EntityFlags.DIRTY)
        self._isDirty = False
        for callback in self._updateCallbacks:
            callback(self)
        self._onUpdateType(self)
        Entity._onUpdateType(self)
    
    @classmethod
    def _onUpdateType(cls, obj):
        """
        Invoked when an entity of 'cls' type has been updated in the database.
        """
        for callback in cls._UPDATE_CALLBACKS:
            callback(obj)        
            
    def _onDelete(self):
        """
        Invoked when the entity has been deleted from the database.
        """
        self._isNew = False
        for callback in self._deleteCallbacks:
            callback(self)
        self._onDeleteType(self)
        Entity._onDeleteType(self)
    
    @classmethod
    def _onDeleteType(cls, obj):
        """
        Invoked when an entity of 'cls' type has been deleted from the datbase.
        """
        for callback in cls._DELETE_CALLBACKS:
            callback(obj)          

    def _getPrimaries(self):
        """
        Returns the current entity's primary field values
        """
        return dict(filter(lambda x: x[0] in self.PRIMARY, self._values.items()))
    
    def _getNonAutoPrimaries(self):
        """
        Returns the current entity's primary field values, ignoring fields that AUTOINCREMENT.
        """
        return dict(filter(lambda x: x[0] in self.PRIMARY and not structs.Attributes.AUTOINCREMENT in self.FIELDS[x[0]].attributes, self._values.items()))
    
    def _getLocalUniqueID(self):
        """
        Returns a local unique ID based upon an entity's unique field values and non-auto primary field values.
        """
        localUniques = self._getLocalUniques()        
        try:
            return "__".join(map(lambda x: self._values[x], localUniques))
        except:
            return ""
            
    def _getUniques(self):
        """
        Return the current entity's unique field values.
        """
        return dict(filter(lambda x: x[0] in self.UNIQUE, self._values.items()))

    def _getLocalUniques(self):
        """
        Returns the current entity's local unique field values, which includes the unique field values and non-auto primary field values.
        """
        return dict(self._getNonAutoPrimaries().items() + self._getUniques().items())

    def __getattr__(self, name):
        """
        Retrieves an attribute.
        """
        if name == "uniqueID":
            return self._getLocalUniqueID()
        elif name == "values":
            return self._values
        elif name in self._values:
            return self._values[name]
        elif name in self._referenceValues:
            return self._referenceValues[name]
        elif name in self._data:
            return self._data[name]
        raise AttributeError("No attribute defined named '%s'" % name)      
    
    def __setattr__(self, name, value):
        """
        Sets an attribute.
        """
        if name in self.__dict__:
            super(Entity, self).__setattr__(name, value)
            return        
        if self.isDeleted():
            raise Exception("Cannot set attributes - entity is deleted.")
            return            
        if self.isClosed():
            raise Exception("Cannot set attributes - entity is closed.")
            return            
        if name in self.FIELDS:
            if name in (self.PRIMARY + self.UNIQUE):
                raise AttributeError("Cannot set a primary or unique attribute value.")
                return
            self._values[name] = value
        elif name in self.REFERENCES:
            expectedType = self.REFERENCES[name].referenceType
            actualType = type(value)
            if not isinstance(value, expectedType):
                raise TypeError("Expecting an object of type '%s' for '%s', got '%s'." % (exceptedType.__name__, name, actualType.__name__))
                return
            self._referenceValues[name] = value
        else:
            self._data[name] = value
        self._onChange({name: value})
    
    def _setValue(self, name, value):
        """
        A private method for setting values with fewer restrictions.
        """
        if self.isDeleted():
            raise Exception("Cannot set attributes - entity is deleted.")
            return            
        if self.isClosed():
            raise Exception("Cannot set attributes - entity is closed.")
            return            
        if name in self.FIELDS:
            self._values[name] = value
        elif name in self.REFERENCES:
            expectedType = self.REFERENCES[name].referenceType
            actualType = type(value)
            if not isinstance(value, expectedType):
                raise TypeError("Expecting an object of type '%s' for '%s', got '%s'." % (exceptedType.__name__, name, actualType.__name__))
                return
            self._referenceValues[name] = value
        else:
            self._data[name] = value
        self._onChange({name: value})
    
    def __delattr__(self, name):
        """
        Delete an attribute - raises an error.
        """
        raise AttributeError("Cannot delete attribute named '%s'" % name)
    
    def __getitem__(self, name):
        """
        Retrieves an item.
        """
        return self.__getattr__(self, name)
    
    def __setitem__(self, name, value):
        """
        Sets an item.
        """
        self.__setattr__(self, name, value)

    def __delitem__(self, name):
        """
        Deletes an item - raises an error.
        """
        self.__delattr__(name)

    def _pullDatabaseValues(self):
        """
        Runs a select query given an entity's local unique values as conditions and returns the first result.
        """
        uniques = self._getLocalUniques()
        conditions = []
        for k,v in uniques.items():
            conditions.append(Conditional(k, v))                
        return self.selectOneBasic(self._db, conditions)
        
    def _mergeValues(self, dbValues):
        """
        Method for merging local values with database values upon first insert/update.
        """        
        self._values = dbValues
        self._onChange(dbValues)        
        
    def isDirty(self):
        """
        Check the entity's flags to see if the entity is dirty.
        """
        return (self._flags & EntityFlags.DIRTY) == EntityFlags.DIRTY

    def isNew(self):
        """
        Check the entity's flags to see if the entity is new.
        """
        return (self._flags & EntityFlags.NEW) == EntityFlags.NEW
    
    def isDeleted(self):
        """
        Check the entity's flags to see if the entity is deleted.
        """
        return (self._flags & EntityFlags.DELETED) == EntityFlags.DELETED
    
    def isClosed(self):
        """
        Check the entity's flags to see if the entity is closed.
        """
        return (self._flags & EntityFlags.CLOSED) == EntityFlags.CLOSED
    
    def _dereferenceValues(self):
        """
        A private method which fills in the referenced fields given the entity objects assigned.
        """
        for referenceKey,referenceValue in self._referenceValues.items():
            referencePrimaryKeys = self.REFERENCES[referenceKey].referenceType.PRIMARY
            for primaryKey in referencePrimaryKeys:
                self._values[primaryKey] = referenceValue[primaryKey]           
    
    @classmethod
    def buildTable(cls, db):
        db.buildTable(cls.TABLE, cls.FIELDS, cls.PRIMARY, cls.UNIQUE)
        
    @classmethod
    def dropTable(cls, db):
        db.dropTable(cls.TABLE)    
        
    def insert(self):
        """
        Inserts the entity into the database.
        """
        print "INSERT"
        if self.isDeleted() or self.isClosed() or not self.isNew():
            return False
        try:
            self._dereferenceValues()
        except:        
            return False               
        try:
            self._db.insert(self.TABLE, self._values)
            self._values = self._pullDatabaseValues()
        except:
            self._mergeValues(self._pullDatabaseValues())
        finally:
            self._onInsert()        
            self._onUpdate()
            return True
        
    def update(self):
        """
        Updates the entity in the database.
        """
        if self.isDeleted() or self.isClosed():
            return False
        if self.isNew():
            self.insert()
        elif self.isDirty():
            try:
                self._dereferenceValues()
            except:
                return False
            self._db.update(self.TABLE, self._values, self._getPrimaries())
        self._onUpdate()
        return True
    
    def delete(self):
        """
        Deletes the entity from the database.
        """
        if self.isDeleted() or self.isClosed():
            return False
        if not self.isNew():
            self._db.delete(self.TABLE, self._getPrimaries())
            self._onDelete()
            return self.close()
            
    def close(self):
        """
        Closes the entity - removes it from the local cache and prevents any changes from being made to the entity.
        """
        if self.isClosed():
            return False
        self._flags = self._flags | EntityFlags.CLOSED
        self._removeFromLocalCache(self)
        return True
    
    @classmethod
    def select(cls, db, conditionals=None, orderFields=None, offset=0, count=0):
        """
        Class method which will return a list of entities of 'cls' type given certain options.
        """
        if cls.REFERENCES is None or len(cls.REFERENCES) == 0:                
            results = cls.selectBasic(db, conditionals, orderFields, offset, count)
            objects = []
            for result in results:
                newObject = cls(db, **result)
                for key, value in newObject.REFERENCES.items():
                    referenced = True
                    for primaryKey in value.referenceType.PRIMARY:
                        if primaryKey not in result:
                            referenced = False
                            break
                    if referenced:
                        conditionals = []
                        for primaryKey in value.referenceType.PRIMARY:
                            conditionals.append(Conditional(primaryKey, result[primaryKey]))
                        newObject[key] = value.referenceType.selectOne(db, conditionals)                                    
                objects.append(newObject)                
            return objects
        else:
            pass
    
    @classmethod
    def selectOne(cls, db, conditionals=None):
        """
        Just like select(), but returns only the first result.
        """
        return cls.select(db, conditionals, None, 0, 1)
    
    @classmethod
    def selectBasic(cls, db, conditionals=None, orderFields=None, offset=0, count=0):
        """
        A method which will return a list of dictionaries given certain options.
        This does not automatically build up entities, so is useful only when working with lots of data in a raw manner.
        """
        return db.select(cls.TABLE, conditionals, None, orderFields, offset, count)        

    @classmethod
    def selectOneBasic(cls, db, conditionals=None):
        """
        A method like selectBasic(), but returns only the first result.
        """
        return db.select(cls.TABLE, conditionals, None, orderFields, 0, 1)[0]        
    
    def view(self, viewMode):
        """
        A method for returning a view of an entity in a specific view mode.
        """
        return self._view(self, viewMode)
    
    @classmethod
    def _view(cls, obj, viewMode):
        """
        A private method for returning a view of an entity in a specific view mode.
        """
        if viewMode in cls.VIEWS:
            return cls.VIEWS[viewMode].invoke(obj)
        return ""        
    
    @classmethod
    def addToViewMode(cls, viewMode, viewCallback):
        if viewMode not in cls.VIEWS:
            cls.VIEWS[viewMode] = [viewCallback]
        else:
            cls.VIEWS[viewMode].viewCallbacks.append(viewCallback)
        
    def registerOnInsert(self, callback):
        """
        Registers a method as a callback, which is invoked when the entity is inserted.
        """
        self._insertCallbacks.append(callback)
    
    def unregisterOnInsert(self, callback):
        """
        Unregisters an 'insert' callback.
        """
        self._insertCallbacks.remove(callback)

    def registerOnChange(self, callback):
        """
        Registers a method as a callback, which is invoked when the entity is changed.
        """
        self._changeCallbacks.append(callback)

    def unregisterOnChange(self, callback):
        """
        Unregisters a 'change' callback.
        """
        self._changeCallbacks.remove(callback)

    def registerOnUpdate(self, callback):
        """
        Registers a method as a callback, which is invoked when the entity is updated.
        """
        self._updateCallbacks.append(callback)
        
    def unregisterOnUpdate(self, callback):
        """
        Unregisters an 'update' callback.
        """
        self._updateCallbacks.remove(callback)
        
    def registerOnDelete(self, callback):
        """
        Registers a method as a callback, which is invoked when the entity is deleted.
        """
        self._deleteCallbacks.append(callback)
    
    def unregisterOnDelete(self, callback):
        """
        Unregisters a 'delete' callback.
        """
        self._deleteCallbacks.remove(callback)        
        
    @classmethod
    def registerOnTypeInsert(cls, callback):
        """
        Registers a method as a callback, which is invoked when an entity of 'cls' type is inserted.
        """
        cls._INSERT_CALLBACKS.append(callback)
    
    @classmethod
    def unregisterOnTypeInsert(cls, callback):
        """
        Unregisters an 'insert' of 'cls' type callback.
        """
        cls._INSERT_CALLBACKS.remove(callback)

    @classmethod
    def registerOnTypeChange(cls, callback):
        """
        Registers a method as a callback, which is invoked when an entity of 'cls' type is changed.
        """
        cls._CHANGE_CALLBACKS.append(callback)

    @classmethod
    def unregisterOnTypeChange(cls, callback):
        """
        Unregisters a 'change' of 'cls' type callback.
        """
        cls._CHANGE_CALLBACKS.remove(callback)
        
    @classmethod
    def registerOnTypeUpdate(cls, callback):
        """
        Registers a method as a callback, which is invoked when an entity of 'cls' type is updated.
        """
        cls._UPDATE_CALLBACKS.append(callback)
        
    @classmethod
    def unregisterOnTypeUpdate(cls, callback):
        """
        Unregisters an 'update' of 'cls' type callback.
        """
        cls._UPDATE_CALLBACKS.remove(callback)
    
    @classmethod    
    def registerOnTypeDelete(cls, callback):
        """
        Registers a method as a callback, which is invoked when an entity of 'cls' type is deleted.
        """
        cls._DELETE_CALLBACKS.append(callback)
    
    @classmethod    
    def unregisterOnTypeDelete(cls, callback):
        """
        Unregisters a 'delete' of 'cls' type callback.
        """
        cls._DELETE_CALLBACKS.remove(callback)