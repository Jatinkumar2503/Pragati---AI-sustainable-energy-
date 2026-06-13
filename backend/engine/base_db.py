import abc
import pandas as pd

class BaseDatabase(abc.ABC):
    """
    Abstract Base Class defining the standard interface for all Database Engines
    in the PRAGATI AI telemetry platform.
    """
    
    @abc.abstractmethod
    def init_db(self) -> None:
        """
        Initializes the database schema, tables, indices, and bootstraps data if empty.
        """
        pass
        
    @abc.abstractmethod
    def insert_telemetry_records(self, records: list, sync: bool = False) -> int:
        """
        Inserts a batch of telemetry records.
        Returns the number of successfully queued/inserted records.
        """
        pass
        
    @abc.abstractmethod
    def query_all_telemetry(self) -> pd.DataFrame:
        """
        Queries all telemetry records from the database, sorted by date ascending.
        """
        pass
        
    @abc.abstractmethod
    def query_recent_telemetry(self, days: int) -> pd.DataFrame:
        """
        Queries the most recent N days of telemetry logs.
        """
        pass
        
    @abc.abstractmethod
    def clear_all_telemetry(self) -> None:
        """
        Deletes all telemetry logs from the database table.
        """
        pass
        
    @abc.abstractmethod
    def close(self) -> None:
        """
        Safely flushes remaining queues and closes open database connection pools.
        """
        pass
