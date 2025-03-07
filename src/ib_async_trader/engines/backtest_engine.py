import asyncio

from datetime import datetime, timedelta
from time import time

from ..brokers.backtest_broker import BacktestBroker
from ..datas.data_file import DataFile
from ..engine import Engine
from ..strategy import Strategy


class BacktestEngine(Engine):
    
    def __init__(self, strategy: Strategy, datas: dict[str, DataFile], 
                 time_step: timedelta, start_time: datetime, end_time: datetime,
                 start_cash: float = 10000):
        super().__init__(strategy, datas)
        
        self.broker = BacktestBroker(datas, start_cash)
        self.strategy.broker = self.broker
        self.start_time = start_time
        self.end_time = end_time
        
        self.walltime_start: int = None
        self.walltime_end: int = None
        self.run_walltime: int = None

        # Set the current time for the backtest and the Strategy 
        self.time_step = time_step
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
        
        for _, data in self.datas.items():
            data.initialize(self.strategy.on_data_update)
        
        self.strategy.on_start()
        
        # TODO: An alternative to incrementing timestep in this manner would be
        # to use the datetime index from a "main" data-source.  This may yeild 
        # performance enhancements since it would not run over dates for which 
        # theres no actual data.
        while self.time_now <= self.end_time:

            # Get the current state (time and stock quote data at that time).
            self.strategy.time_now = self.time_now
            
            # Set each data's perception of the current time
            data: DataFile
            for _, data in self.datas.items():
                data.set_time(self.time_now)
            
            # Set the broker's perception of the current time
            self.broker.time_now = self.time_now
            
            # Engage the strategy, which will decide what actions to take on the 
            # account given the current state.
            asyncio.run(self.strategy.tick())
            
            # Perform an update on the account so it can effect any actions 
            # taken on it by the stategy.  The update will return lists of 
            # actions that were taken, which will be stored in prev_actions
            # and passed to the strategy on the next tick.
            self.broker.update()
            
            # Advance the current time
            self.time_now += self.time_step
            

        self.walltime_end = time()
        self.run_walltime = self.walltime_end - self.walltime_start    
        self.strategy.on_finish()
