def enum(**enums):
    """
    A method that returns a class which closely mimics an enumeration.
    """
    return type('Enum', (), enums)

"""
Enum of different conditions.
"""    
Condition = enum(AND="AND", OR="OR", EQUAL="=", NOT_EQUAL="<>", LESS="<", GREATER=">", LESS_OR_EQUAL="<=", GREATER_OR_EQUAL=">=", CONTAINS="LIKE")

"""
Enum of different ordering.
"""                 
Ordering = enum(DESCENDING="DESC", ASCENDING="ASC")

"""
Enum of different field types.
"""               
Types = enum(INT="INT", FLOAT="FLOAT", VARCHAR="VARCHAR", TEXT="TEXT", BLOB="BLOB")

"""
Enum of different field attributes.
"""
Attributes = enum(UNSIGNED="UNSIGNED", AUTOINCREMENT="AUTO_INCREMENT", NOT_NULL="NOT NULL")

"""
Enum of different join types.
"""
Joins = enum(INNER="INNER JOIN", LEFT_OUTER="LEFT OUTER JOIN", RIGHT_OUTER="RIGHT OUTER JOIN", FULL_OUTER="FULL OUTER JOIN", CROSS="CROSS JOIN")

class Field(object):
    """
    A class that defines the properties of a field.
    """
    fieldType = None
    default = None
    length = None
    attributes = () 
    def __init__(self, fieldType, default=None, length=None, attributes=()):
        self.fieldType = fieldType
        self.default = default
        self.length = length
        self.attributes = attributes               

class FieldReference(object):
    """
    A class that defines a reference to an entity type, to infer additional fields.
    """
    referenceType = None
    def __init__(self, referenceType):
        self.referenceType = referenceType

class Conditional(object):
    """
    A class that defines a conditional statement.
    """
    field = None
    value = None
    argument = Condition.EQUAL
    def __init__(self, field, value, argument=Condition.EQUAL):
        self.field = field
        self.value = value
        self.argument = argument

class TableJoin(object):
    """
    A class that defines a table join.
    """
    leftTable = None
    rightTable = None
    joinType = Joins.INNER
    fieldJoins = ()
    def __init__(self, leftTable, rightTable, fieldJoins, joinType=Joins.INNER):
        self.leftTable = leftTable
        self.rightTable = rightTable
        self.joinType = joinType
        self.fieldJoins = fieldJoins

class FieldJoin(object):
    """
    A class that defines a field join.
    """
    leftField = None
    rightField = None
    argument = Condition.EQUAL
    def __init__(self, leftField, rightField=None, argument=Condition.EQUAL):
        self.leftField = leftField
        if self.rightField is None:
            self.rightField = self.leftField
        else:
            self.rightField = rightField
        self.argument = argument            