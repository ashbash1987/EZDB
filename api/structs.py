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
    def __init__(self, *a):
        if len(a) >= 2:
            self.field = a[0]
            self.value = a[1]        
        if len(a) >= 3:
            self.argument = a[2]        

                                                          