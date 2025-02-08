import pandas as pd

from ib_async import BarDataList, IB, Contract, RealTimeBar, util

from ..data import Data


class DataStream(Data):
        
    def __init__(self, 
                 contract: Contract, 
                 bar_size_s: int, 
                 what_to_show: str = "TRADES",
                 process_data: callable = None, 
                 process_data_args: dict = {}):
        super().__init__(contract)
        self.bar_size_s = bar_size_s 
        self.what_to_show = what_to_show
        self.process_data = process_data
        self.process_data_args = process_data_args
        self.ib: IB = None
        self._five_sec_bars: BarDataList = None
        self.is_first_update = True
        
        
    async def initialize(self, ib: IB) -> None:
        self.ib = ib
        await self.ib.qualifyContractsAsync(self.contract)
        self._five_sec_bars = await self.ib.reqHistoricalDataAsync(
            self.contract, endDateTime="", durationStr="2 D",
            barSizeSetting="5 secs", whatToShow=self.what_to_show, useRTH=False, 
            keepUpToDate=True)        
        self._five_sec_bars.updateEvent += self._on_update
        
                
    async def _on_update(self, bars: list[RealTimeBar], has_new: bool):
        if len(bars) < 1:
            print("WARNING: Data updated but no bars were provided.")
            return
        
        if has_new:
            
            # Convert RealTimeBar list to dataframe
            bars_df = util.df(
                bars, 
                labels=('date', 'open', 'high', 'low', 'close', 'volume')
            )
            
            # Dates from ibkr don't appear to account for DST
            # This massages the date data to account for DST and then 
            # converts the DataFrame index to a DatetimeIndex
            bars_df.index = pd.DatetimeIndex(
                bars_df["date"].dt.tz_convert("US/Eastern"))
            bars_df.drop('date', axis=1, inplace=True)
        
            # Resample the data to the requested time interval
            bars_df = bars_df.resample(f"{self.bar_size_s}s").agg(
                {
                    'open':'first',
                    'high':'max',
                    'low':'min',
                    'close':'last',
                    'volume':'sum'
                }).dropna(how='any')
    
            # Do any user-specified processing here
            if self.process_data:
               bars_df = await self.process_data(bars_df, self.is_first_update, **self.process_data_args)
    
            # Update the data on the strategy, set current tick time
            # and call tick() function 
            self._df = bars_df
            self.time_now = self._df.iloc[-1].name
            
            self.is_first_update = False
