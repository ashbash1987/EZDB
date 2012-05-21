mysql = None
cursors = None

def selectImplementation(implementation="MySQLdb"):
    """
    Dynamically imports the modules for a specific MySQL implementation.
    """
    global mysql
    global cursors
    mysql = __import__(implementation)
    cursors = __import__("%s.cursors" % implementation)
    
from .. import interface
from .. import structs

def getClass():
    """
    Returns a class generated using the selected MySQL implementation through selectImplementation().
    """
    global mysql
    global cursors
    class MySQL(interface.DBInterface):
        """
        MySQL DB Implementation
        """
        _dbConnector = None
        def __init__(self, database, user, password=None, host="localhost"):
            """
            Initializer.
            """
            self._dbConnector = mysql.connect(host=host,
                                              user=user,
                                              passwd=password, 
                                              db=database,
                                              cursorclass=cursors.DictCursor)
            
        @staticmethod
        def _getToken(value):
            """
            Private static method for returning an appropriate SQL token.
            """
            return "%s"
            
        @staticmethod
        def _getFieldDefinition(values):
            """
            Private static method for returning SQL for field definitions.
            """
            fields = []
            for k, v in values.items():
                fieldType = v.fieldType
                if v.length is not None:
                    fieldType = "%s(%d)" % (fieldType, v.length)                            
                attributes = " ".join(v.attributes)
                if v.default is not None:
                    if isinstance(v.default, str):
                        attributes = "%s DEFAULT '%s'" % (attributes, v.default)
                    else:
                        attributes = "%s DEFAULT %s" % (attributes, str(v.default))
                elif structs.Attributes.NOT_NULL not in v.attributes:
                    attributes = "%s DEFAULT NULL" % attributes
                fields.append("%s %s %s" % (k, fieldType, attributes))
            return ", ".join(fields)                        
        
        @staticmethod
        def _getPrimaryDefinition(primary):
            """
            Private static method for returning SQL for primary key definitions.
            """
            return "PRIMARY KEY (%s)" % (", ".join(primary))
        
        @staticmethod
        def _getUniqueDefinition(unique):
            """
            Private static method for returning SQL for unique key definitions.
            """
            return "UNIQUE KEY `%s` (%s)" % ("_".join(unique), ", ".join(unique))
          
        def buildTable(self, table, fields, primary, unique):
            definitions = []
            definitions.append(MySQL._getFieldDefinition(fields))        
            if primary is not None and len(primary) > 0:        
                definitions.append(MySQL._getPrimaryDefinition(primary))
            if unique is not None and len(unique) > 0:
                definitions.append(MySQL._getUniqueDefinition(unique))        
            query = "CREATE TABLE IF NOT EXISTS `%s` (%s)" % (table, ", ".join(definitions))
            cursor = self._dbConnector.cursor()                
            cursor.execute(query)
            cursor.close()
        buildTable.__doc__ = interface.DBInterface.buildTable.__doc__        
        
        def dropTable(self, table):
            query = "DROP TABLE IF EXISTS `%s`" % table
            cursor = self._dbConnector.cursor()
            cursor.execute(query)
            cursor.close()      
        dropTable.__doc__ = interface.DBInterface.dropTable.__doc__                    
    
        @staticmethod
        def _buildFieldString(fields):
            """
            Private static method for returning SQL of field selections.
            """
            if fields is None or len(fields) == 0:
                return "*"
            return ", ".join(map(lambda x: ("`%s`" % x) if isinstance(x, str) else ("`%s`.`%s` AS %s" % (x.tableName, x.fieldName, x.alias)), fields))
            
        @staticmethod
        def _buildValueTokenString(values):
            """
            Private static method for returning SQL of field initialization.
            """
            return ", ".join(map(lambda x: MySQL._getToken(x), values))
        
        @staticmethod
        def _buildAssignmentString(assignmentValues):
            """
            Private static method for returning SQL of field assignments.
            """            
            return ", ".join(map(lambda x: "`%s`=%s" % (x[0], MySQL._getToken(x[1])), assignmentValues.items()))
        
        @staticmethod
        def _buildOrderString(orderValues):
            """
            Private static method for returning SQL of field ordering statements.
            """
            return ", ".join(map(lambda x: "`%s` %s" % x, orderValues.items()))                
                            
        @staticmethod
        def _buildConditionString(conditionalValues, condition=" AND "):
            """
            Private static method for returning SQL of field conditional statements.
            """
            if conditionalValues is None:
                return ""
            conditionals = []
            for conditional in conditionalValues:
                token = MySQL._getToken(conditional.value)
                conditionals.append("`%s` %s %s" % (conditional.field, conditional.argument, token))
            return condition.join(conditionals)    
            
        def insert(self, table, values, *a):        
            queryArguments = []
            for value in values.values():
                queryArguments.append(value)
            fields = MySQL._buildFieldString(values.keys())
            valuetokens = MySQL._buildValueTokenString(values.values())        
            query = "INSERT %s INTO `%s` (%s) VALUES (%s)" % (" ".join(a), table, fields, valuetokens)        
            cursor = self._dbConnector.cursor()                
            cursor.execute(query, queryArguments)
            cursor.close()
        insert.__doc__ = interface.DBInterface.insert.__doc__                        
            
        def select(self, table, selectFields=None, conditionals=None, orderFields=None, offset=0, count=0):
            queryArguments = []
            fields = MySQL._buildFieldString(selectFields)                
            query = "SELECT %s FROM `%s`" % (fields, table)                  
            
            if conditionals != None:
                for conditional in conditionals:
                    queryArguments.append(conditional.value)                
                conditions = MySQL._buildConditionString(conditionals)
                query = "%s WHERE %s" % (query, conditions)
                            
            if orderFields is not None:
                orders = MySQL._buildOrderString(orderFields)
                query = "%s ORDER BY %s" % (query, orders)
                            
            if offset > 0 or count > 0:
                query = "%s LIMIT %d, %d" % (query, int(offset), int(count))
            
            cursor = self._dbConnector.cursor()
            cursor.execute(query, queryArguments)        
            rows = cursor.fetchall()
            cursor.close()
            return rows         
        select.__doc__ = interface.DBInterface.select.__doc__
        
        def selectJoin(self, baseTable, joins, selectFields, conditionals=None, orderFields=None, offset=0, count=0):
            queryArguments = []
            fields = MySQL._buildFieldString(selectFields)                
            query = "SELECT %s FROM `%s`" % (fields, table)
            
            if joins is not None and len(joins) > 0:
                joinElements = []
                for join in joins:
                    tableJoinStatement = "%s `%s` ON " % (join.joinType, join.rightTable)
                    joinElements.append(tableJoinStatement + (" AND ".join(map(lambda x: "`%s`.`%s`%s`%s`.`%s`" % (join.leftTable, x.leftField, x.argument, join.rightTable, x.rightField), join.fieldJoins))))
                query = "%s %s" % (query, joinElements)                    
            
            if conditionals != None:
                for conditional in conditionals:
                    queryArguments.append(conditional.value)                
                conditions = MySQL._buildConditionString(conditionals)
                query = "%s WHERE %s" % (query, conditions)
                            
            if orderFields is not None:
                orders = MySQL._buildOrderString(orderFields)
                query = "%s ORDER BY %s" % (query, orders)
                            
            if offset > 0 or count > 0:
                query = "%s LIMIT %d, %d" % (query, int(offset), int(count))
            
            cursor = self._dbConnector.cursor()
            cursor.execute(query, queryArguments)        
            rows = cursor.fetchall()
            cursor.close()
            return rows           
        selectJoin.__doc__ = interface.DBInterface.selectJoin.__doc__                                
            
        def update(self, table, values, conditionals):
            queryArguments = []
            for value in values.values():
                queryArguments.append(value)
            for conditional in conditionals:
                queryArguments.append(conditional.value)
            assignments = MySQL._buildAssignmentString(values)
            conditions = MySQL._buildConditionString(conditionals)
            query = "UPDATE `%s` SET %s WHERE %s" % (table, assignments, conditions)
            cursor = self._dbConnector.cursor()
            cursor.execute(query, queryArguments)
            cursor.close()        
        update.__doc__ = interface.DBInterface.update.__doc__                        
            
        def delete(self, table, conditionals):
            queryArguments = []
            for conditional in conditionals:
                queryArguments.append(conditional.value)
            conditions = MySQL._buildConditionString(conditionals)
            query = "DELETE FROM `%s` WHERE %s" % (table, conditions)
            cursor = self._dbConnector.cursor()
            cursor.execute(query, queryArguments)
            cursor.close()        
        delete.__doc__ = interface.DBInterface.delete.__doc__                        
            
        def refresh(self):
            self._dbConnector.commit()
        refresh.__doc__ = interface.DBInterface.refresh.__doc__                        
            
        def close(self):
            self._dbConnector.commit()
            self._dbConnector.close()
        close.__doc__ = interface.DBInterface.close.__doc__                        

    return MySQL                