import dask.dataframe as dd
import pandas as pd

from datetime import datetime, timedelta
from enum import Enum
from ib_async import Contract

from ..data import Data
 

class OptionsModelType(Enum):
    BLACK_SCHOLES = 1
    HISTORICAL_DATA = 2
    NONE = 3
 
 
class DataFile(Data):
    
    def __init__(self, 
                 contract: Contract, 
                 file_path: str, 
                 options_model: OptionsModelType = OptionsModelType.BLACK_SCHOLES,
                 historical_options_parquet_path: str = None):
        super().__init__(contract)
                
        # Read data from the file
        df = pd.read_csv(file_path)
        
        # Convert the date column to datetime
        # I don't like the way pandas converts dates/timezones, so
        # we will always assume data is given in "local time" and we can 
        # ignore the timezone.  Ensuring that the dates/times are correct 
        # in the data is left as an exercise to the reader.
        df["date"]  = df["date"].str[0:19]
        df["date"] = pd.to_datetime(df["date"])
        df.index = pd.DatetimeIndex(df["date"])
        
        # Cleanup duplicates and interpolate missing values
        df = df[~df.index.duplicated(keep='first')]
        # TODO: Probably need to do this for more than just the iv column
        df["iv"] = df["iv"].interpolate(method="linear")
        
        self._df = df
        self.time_now = self._df.index[0]
        
        self.options_model = options_model
        if options_model == OptionsModelType.HISTORICAL_DATA:
            self._historical_options_data = HistoricalOptionsData(historical_options_parquet_path)
        
    
    def initialize(self, on_update = None):
        super().initialize(on_update)
        
        if self.on_update:
            self._df = self.on_update(self.contract.symbol, self._df)
    
        
    def set_time(self, time_now: datetime):
        self.time_now = time_now


class HistoricalOptionsData:
    
    def __init__(self, paquet_path: str):
        self._ddf: dd.DataFrame = dd.read_parquet(paquet_path)
        
        # persist the data in memory to speed up future compute operations
        self._ddf = self._ddf.persist()
        
        
    def get_options_chain_as_of(self, quote_time: datetime, days_ahead: int = 1) -> pd.DataFrame:
        qstr = "QUOTE_UNIXTIME == @quote_unixtime and EXPIRE_DATE >= @exp_min and EXPIRE_DATE <= @exp_max"
        qvars = {
            'quote_unixtime': int(quote_time.timestamp()),
            'exp_min': quote_time.strftime("%Y-%m-%d"),
            'exp_max': (quote_time.date() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
        }
        cols = ["QUOTE_UNIXTIME", "EXPIRE_DATE", "C_DELTA", "C_GAMMA", "C_VEGA", "C_THETA" ,"C_RHO" ,"C_IV" ,"C_VOLUME" ,"C_LAST" ,"C_SIZE" , "C_BID", "C_ASK", "STRIKE", "P_BID", "P_ASK", "P_SIZE", "P_LAST", "P_DELTA", "P_GAMMA", "P_VEGA", "P_THETA", "P_RHO", "P_IV", "P_VOLUME"]
        return self._ddf.query(qstr,  local_dict=qvars)[cols].compute()
        
    
    def get_price_timeseries_for_option(self, exp_date: datetime, strike: float, right: str) -> pd.DataFrame:
        qstr = "EXPIRE_DATE == @exp_date and STRIKE == @strike"
        qvars = {
            'exp_date': exp_date.strftime("%Y-%m-%d"),
            'strike': strike
        }
        cols = ["QUOTE_UNIXTIME", "EXPIRE_DATE", "STRIKE", right + "_LAST", right + "_SIZE", right + "_BID", right + "_ASK", right + "_VOLUME"]
        return self._ddf.query(qstr, local_dict=qvars)[cols].compute()
        