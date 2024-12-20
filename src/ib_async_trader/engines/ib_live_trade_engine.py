import ib_async as ib
import pandas as pd
import threading
import sys

from ..brokers.ib_live_trade_broker import IBLiveTradeBroker
from ..engine import Engine
from ..strategy import Strategy


class IBLiveTradeEngine(Engine):
    
    def __init__(self, strategy: Strategy, time_interval_s: int=5, 
                 process_data: callable = None, process_data_args: dict = {},
                 host: str="127.0.0.1", port: int=7496, client_id: int=1):
        super().__init__(strategy)
        self.time_interval_s = time_interval_s
        self.host = host
        self.port = port
        self.client_id = client_id
        self.process_data = process_data
        self.process_data_args = process_data_args
        self.run_program: bool = False
        self.ib = ib.IB()
        
        self.input_lock = threading.Lock()
        self.user_input = None
    
    
    def _get_input(self):
        while True:
            line = sys.stdin.readline().strip()
            if line:
                with self.input_lock:
                    self.user_input = line
    
    
    def _non_blocking_input(self):
        with self.input_lock:
            return self.user_input
        
    
    def run(self) -> None:
        try:
            self.run_program = True
            self.strategy.broker = IBLiveTradeBroker(self.ib)

            self.ib.connect(self.host, self.port, self.client_id)
            self.ib.qualifyContracts(self.strategy.underlying_contract)

            five_sec_bars = self.ib.reqHistoricalData(
                self.strategy.underlying_contract, endDateTime="", durationStr="2 D",
                barSizeSetting="5 secs", whatToShow="TRADES", useRTH=False, 
                keepUpToDate=True)

            five_sec_bars.updateEvent += lambda bars, has_new: \
                self._process_bars(bars, has_new)

            input_thread = threading.Thread(target=self._get_input, daemon=True)
            input_thread.start()

            # Keep the process alive until a stop is requested by keypress
            while self.run_program:
                inpt = self._non_blocking_input()
                if inpt and inpt == "q":
                    self.run_program = False
                self.ib.sleep(0.01)
        
        finally:
            self.strategy.on_finish()
            self.ib.disconnect()
            sys.exit()
        
        
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
            if self.process_data:
               bars_df = self.process_data(bars_df, **self.process_data_args)
    
            # Update the data on the strategy, set current tick time
            # and call tick() function 
            self.strategy.data = bars_df
            self.strategy.time_now = bars_df.iloc[-1].name
            await self.strategy.tick()
            await self.strategy.post_tick()
