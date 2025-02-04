import pandas as pd

from datetime import datetime
from ib_async import Contract

from ..data import Data
 
 
class DataFile(Data):
    
    def __init__(self, contract: Contract, file_path: str, process_data: callable = None):
        super().__init__(contract)
        
        # Read data from the file
        df = pd.read_csv(file_path)
        
        # Convert the date column to datetime
        df["date"] = pd.to_datetime(df["date"], utc=True)
        df["date"] = df["date"].dt.tz_convert("US/Eastern")
        df["date"] = df["date"].dt.tz_localize(None)
        df.index = pd.DatetimeIndex(df["date"])
        
        # Cleanup duplicates and interpolate missing values
        df = df[~df.index.duplicated(keep='first')]
        # TODO: Probably need to do this for more than just the iv column
        df["iv"] = df["iv"].interpolate(method="linear")
        
        if process_data:
            self._df = process_data(df, 7)
        else: 
            self._df = df
        
        self.time_now = self._df.index[0]
        
        
    def set_time(self, time_now: datetime):
        self.time_now = time_now
