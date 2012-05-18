import sqlite3

from .. import interface
from .. import structs

class SQLite(interface.DBInterface):
    """
    SQLite DB Implementation
    """
    _dbConnector = None
    def __init__(self, database):
        """
        Initializer.
        """
        self._dbConnector = sqlite3.connect(database)
        self._dbConnector.row_factory = SQLite._sqliteRowFactory
        
    @staticmethod
    def _sqliteRowFactory(cursor, row):
        """
        Private method for returning database rows as dictionaries. Much like using DictCursor in MySQLdb/pymysql.
        """
        d = {}
        for idx,col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d
        
    @staticmethod
    def _getFieldDefinition(values):
        """
        Private static method for returning SQL for field definitions.
        """
        fields = []
        for k, v in values:
            fieldType = v.fieldType
            if v.length is not None:
                fieldType = "%s(%d)" % (fieldType, v.length)                
            attributes = []
            if structs.Attributes.AUTOINCREMENT in v.attributes:
                attributes.append("AUTOINCREMENT")
            if structs.Attributes.NOT_NULL in v.attributes:
                attributes.append(structs.Attributes.NOT_NULL)                                                            
            attributes = " ".join(attributes)
            if v.default is not None:
                if isinstance(v.default, str):
                    attributes = "%s DEFAULT '%s'" % (attributes, v.default)
                else:
                    attributes = "%s DEFAULT %s" % (attributes, str(v.default))
            elif structs.Attributes.NOT_NULL not in v.attributes:
                attributes = "%s DEFAULT NULL" % attributes
            fields.append("%s %s" % (fieldType, attributes))
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
        return "UNIQUE (%s)" % ("_".join(unique), ", ".join(unique))
      
    def buildTable(self, table, fields, primary, unique):
        definitions = []
        definitions.append(SQLite._getFieldDefinition(fields))        
        if primary is not None:        
            definitions.append(SQLite._getPrimaryDefinition(primary))
        if unique is not None:
            definitions.append(SQLite._getUniqueDefinition(unique))        
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
    def _getToken(value):
        """
        Private static method for returning an appropriate SQL token.
        """
        return "?"

    @staticmethod
    def _buildFieldString(fields):
        """
        Private static method for returning SQL of field selections.
        """
        if fields is None:
            return "*"
        return ", ".join(map(lambda x: "`%s`" % x, fields))
        
    @staticmethod
    def _buildValueTokenString(values):
        """
        Private static method for returning SQL of field initialization.
        """
        tokens = []        
        for value in values.values():
            tokens.append(SQLite._getToken(value))
        return ", ".join(tokens)
    
    @staticmethod
    def _buildAssignmentString(assignmentValues):
        """
        Private static method for returning SQL of field assignments.
        """
        assignments = []
        for k,v in assignmentValues.items():
            token = SQLite._getToken(v)
            assignments.append("`%s`=%s" % (k, token))
        return ", ".join(assignments)
    
    @staticmethod
    def _buildOrderString(orderValues):
        """
        Private static method for returning SQL of field ordering statements.
        """
        orders = []
        for k,v in orderValues.items():
            orders.append("`%s` %s" % (k, v))
        return ", ".join(orders)                
                        
    @staticmethod
    def _buildConditionString(conditionalValues, condition=" AND "):
        """
        Private static method for returning SQL of field conditional statements.
        """
        if conditionalValues is None:
            return ""
        conditionals = []
        for conditional in conditionalValues:
            token = SQLite._getToken(conditional.value)
            conditionals.append("`%s`%s%s" % (conditional.field, conditional.argument, token))
        return condition.join(conditionals)  
        
    def insert(self, table, values, *a):
        queryArguments = []
        for value in values.values():
            queryArguments.append(value)
        fields = SQLite._buildFieldString(values.keys())
        valuetokens = SQLite._buildValueTokenString(values.values())        
        query = "INSERT %s INTO `%s` (%s) VALUES (%s)" % (" ".join(a), table, fields, valuetokens)        
        cursor = self._dbConnector.cursor()                
        cursor.execute(query, queryArguments)
        cursor.close()        
    insert.__doc__ = interface.DBInterface.insert.__doc__                        
        
    def select(self, table, conditionals=None, selectFields=None, orderFields=None, offset=0, count=0):
        queryArguments = []
        fields = SQLite._buildFieldString(selectFields)                
        query = "SELECT %s FROM `%s`" % (fields, table)
        if conditionals != None:
            for conditional in conditionals:
                queryArguments.append(conditional.value)                
            conditions = SQLite._buildConditionString(conditionals)
            query = "%s WHERE %s" % (query, conditions)            
        if orderFields is not None:
            orders = SQLite._buildOrderString(orderFields)
            query = "%s ORDER BY %s" % (query, orders)            
        if offset > 0 or count > 0:
            query = "%s LIMIT %d, %d" % (query, int(offset), int(count))
        cursor = self._dbConnector.cursor()
        cursor.execute(query, queryArguments)        
        rows = cursor.fetchall()
        cursor.close()
        return rows       
    select.__doc__ = interface.DBInterface.select.__doc__                        
        
    def update(self, table, values, conditionals):
        queryArguments = []
        for value in values.values():
            queryArguments.append(value)
        for conditional in conditionals:
            queryArguments.append(conditional.value)
        assignments = SQLite._buildAssignmentString(values)
        conditions = SQLite._buildConditionString(conditionals)
        query = "UPDATE `%s` SET %s WHERE %s" % (table, assignments, conditions)
        cursor = self._dbConnector.cursor()
        cursor.execute(query, queryArguments)
        cursor.close()        
    update.__doc__ = interface.DBInterface.update.__doc__                        
        
    def delete(self, table, conditionals):
        queryArguments = []
        for conditional in conditionals:
            queryArguments.append(conditional.value)
        conditions = SQLite._buildConditionString(conditionals)
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
                                   