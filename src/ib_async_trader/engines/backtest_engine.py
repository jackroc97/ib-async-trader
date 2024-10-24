import pandas as pd
import asyncio

from datetime import datetime
from time import time

from ..brokers.backtest_broker import BacktestBroker
from ..engine import Engine
from ..strategy import Strategy


class BacktestEngine(Engine):
    
    def __init__(self, strategy, data: pd.DataFrame, start_cash: float = 10000,
                 start_time: datetime = None, end_time: datetime = None):
        super().__init__(strategy)
        
        self.strategy: Strategy = strategy
        self.broker = BacktestBroker(start_cash)
        self.strategy.broker = self.broker
        
        self.walltime_start: int = None
        self.walltime_end: int = None
        self.run_walltime: int = None
        
        self.data: pd.DataFrame = data
        
        # Get the start and end time of the backtest
        self.start_time: datetime = start_time or self.data.index[0]
        self.end_time: datetime = end_time or self.data.index[-1]
        
        # Select only data points that are between the start end end date
        self.data = self.data[(self.data.index >= self.start_time) & \
            (self.data.index <= self.end_time)]

        # Set data on the user's `strategy`
        self.strategy.data = self.data

        # Set the current time for the backtest and the Strategy 
        self.time_now: datetime = self.start_time
        self.strategy.time_now = self.time_now

        
        
    def run(self) -> tuple[list, list]:
        """
        The `Backtest.run()` method is the main loop of the backtest.  Each 
        timepoint in `Backtest.data` is ticked through and passed to 
        `Backtest.strategy`, which can then make decisions based on that data.
        The `Backtest.account` is also updated each tick.

        Returns:
            tuple[list, list]: The fist list in the tuple is time-series data
            of the account state throughout the backtest.  The second is a list
            of all trades made during the backtest.  These lists can be used
            for post-processing and evaluating the efficay of a strategy.
        """
        
        self.walltime_start = time()
        
        # Initialize the account with the backtest start time.
        self.broker.initialize(self.start_time)
        
        for dt, row in self.data.iterrows():

            # Get the current state (time and stock quote data at that time).
            self.time_now: datetime = dt.to_pydatetime()
            self.strategy.time_now = self.time_now
            
            # Engage the strategy, which will decide what actions to take on the 
            # account given the current state.
            asyncio.run(self.strategy.tick())
            
            # Perform an update on the account so it can effect any actions 
            # taken on it by the stategy.  The update will return lists of 
            # actions that were taken, which will be stored in prev_actions
            # and passed to the strategy on the next tick.
            self.broker.update(self.time_now, row)
            
            self.prev_time = self.time_now
        
        self.walltime_end = time()
        self.run_walltime = self.walltime_end - self.walltime_start    
        self.strategy.on_finish()
