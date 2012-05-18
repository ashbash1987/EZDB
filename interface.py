class DBInterface(object):
    """
    An 'abstract' class that should be inherited to provide different database implementations that work with a simplified database API.
    """
    def __init__(self):
        """
        Initializer.
        """
        raise NotImplementedError("Inheriting class should provide '__init__'")
    
    def buildTable(self, table, fields, primary=None, unique=None):
        """
        Method for building a table definition.
        """
        raise NotImplementedError("Inheriting class should provide 'buildTable'")
    
    def dropTable(self, table):
        """
        Method for dropping a table and its definition.
        """
        raise NotImplementedError("Inheriting class should provide 'dropTable'")

    def insert(self, table, values):
        """
        Method for inserting a row into a table.
        """
        raise NotImplementedError("Inheriting class should provide 'insert'")
        
    def select(self, table, conditionals=None, selectFields=None, orderFields=None, offset=0, count=0):
        """
        Method for selecting rows from a table given certain options.
        """
        raise NotImplementedError("Inheriting class should provide 'select'")
    
    def selectJoin(self, baseTable, joins, conditionals=None, selectFields=None, orderFields=None, offset=0, count=0):
        """
        Method for selecting rows from a table given certain options, along with joins.
        """
        raise NotImplementedError("Inheriting class should provide 'selectJoin'")
        
    def update(self, table, values, conditionals):
        """
        Method for updating rows in a table given certain conditions.
        """
        raise NotImplementedError("Inheriting class should provide 'update'")
        
    def delete(self, table, conditionals):
        """
        Method for deleting rows in a table given certain conditions.
        """
        raise NotImplementedError("Inheriting class should provide 'delete'")
    
    def refresh(self):
        """
        Method for refreshing the database (e.g. committing transactions).
        """
        raise NotImplementedError("Inheriting class should provide 'refresh'")
    
    def close(self):
        """
        Method for closing the database.
        """
        raise NotImplementedError("Inheriting class should provide 'close'")