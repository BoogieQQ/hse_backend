import time


from typing import Callable, Any
from functools import wraps
from metrics import DB_QUERY_DURATION
from metrcis_constants import QueryType, TableName

def track_db_query(query_type: QueryType, table: TableName):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                DB_QUERY_DURATION.labels(
                    query_type=query_type,
                    table=table
                ).observe(duration)
        return wrapper
    return decorator