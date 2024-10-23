import ib_async as ib
import pandas as pd

from datetime import time

from ..brokers.ib_live_trade_broker import IBLiveTradeBroker
from ..engine import Engine
from ..strategy import Strategy


class IBLiveTradeEngine(Engine):
    
    def __init__(self, strategy: Strategy, time_interval_s: int=5, 
                 host: str="127.0.0.1", port: int=7496, client_id: int=1, 
                 data_processor: callable = None):
        super().__init__(strategy)
        self.time_interval_s = time_interval_s
        self.host = host
        self.port = port
        self.client_id = client_id
        self.data_processor = data_processor
        self.ib = ib.IB()
        
    
    def run(self, start_time: time=None, end_time: time=None) -> None:
        self.strategy.broker = IBLiveTradeBroker(self.ib)
        
        self.ib.connect(self.host, self.port, self.client_id)
        self.ib.qualifyContracts(self.strategy.underlying_contract)
        
        five_sec_bars = self.ib.reqHistoricalData(
            self.strategy.underlying_contract, endDateTime="", durationStr="2 D",
            barSizeSetting="5 secs", whatToShow="TRADES", useRTH=False, 
            keepUpToDate=True)

        five_sec_bars.updateEvent += lambda bars, has_new: \
            self._process_bars(bars, has_new)

        # Keep the process alive for the specified time
        time_range = self.ib.timeRange(start_time, end_time, 1)
        for _ in time_range:
            self.ib.sleep(0.01)
        
        self.strategy.on_finish()
        self.strategy.chart.show(block=True)
        
        
    async def _process_bars(self, bars: list[ib.RealTimeBar], 
                      has_new_bar: bool) -> None:
        
        if has_new_bar:
            
            # Convert RealTimeBar list to dataframe
            bars_df = ib.util.df(
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
            bars_df = bars_df.resample(f"{self.time_interval_s}s").agg(
                {
                    'open':'first',
                    'high':'max',
                    'low':'min',
                    'close':'last',
                    'volume':'sum'
                }).dropna(how='any')
    
            # Do any user-specified processing here
            if self.data_processor:
                bars_df = self.data_processor(bars_df)
    
            # Update the data on the strategy, set current tick time
            # and call tick() function 
            self.strategy.data = bars_df
            self.strategy.time_now = bars_df.iloc[-1].name
            await self.strategy.tick()
            self.strategy.update_live_chart()
            