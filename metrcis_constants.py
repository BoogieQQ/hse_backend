from enum import Enum

class QueryType(str, Enum):
    CREATE = "create"
    SELECT = "select"
    UPDATE = "update"
    DELETE = "delete"
    EXISTS = "exists"
    TRUNCATE = "truncate"

class TableName(str, Enum):
    ADVERTISEMENTS = "advertisements"
    USERS = "users"
    ACCOUNT = "account"
    MODERATION = 'moderations'