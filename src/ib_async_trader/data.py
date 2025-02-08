import pandas as pd

from datetime import datetime
from ib_async import Contract


class Data:
    
    def __init__(self, contract: Contract):
        self._df = pd.DataFrame()
        self.time_now: datetime = None
        self.contract = contract
        
        
    def get(self, name: str, bars_ago: int = 0) -> any:
        """
        Get a single cell of data from the underlying DataFrame at the current
        time, or a specified number of "bars ago".

        Args:
            name (str): The name of the data to be retrieved (e.g. "open" or
                "close").  
            bars_ago (int, optional): A number of bars back to get the data, 
                counting backwards from the current backtest time.  
                Defaults to 0.

        Returns:
            any: The requested data at the current time or specified number of
                "bars ago".
        """
        
        # NOTE: If an error is caused here by get_loc returning more than one 
        # value, the most likely culprit is duplicate data.
        if self.time_now in self._df.index:
            idx = self._df.index.get_loc(self.time_now) - bars_ago
            return self._df.iloc[idx][name]
        else:
            return None
    
    
    def get_last(self, name: str):
        last_time = self._df.index.asof(self.time_now)
        idx = self._df.index.get_loc(last_time)
        return self._df.iloc[idx][name]


    def exists(self, time: datetime=None):
        time = time or self.time_now
        return time in self._df.index
    
    
    def as_df(self) -> pd.DataFrame:
        return self._df
