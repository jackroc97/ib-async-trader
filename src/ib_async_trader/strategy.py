from datetime import datetime

import pandas as pd
import ib_async as ib

from .broker import Broker


class Strategy:
    """
    The `Strategy` class is an abstract class that is designed to provided a 
    basic framework for making custom strategies to be run in a backtest.  A 
    user's custom strategies should inherit from this class and implement its
    methods.
    """
    
    def __init__(self, underlying_contract: ib.Contract):
        """Initialize a `Strategy` object."""
        self.underlying_contract = underlying_contract
        self.broker: Broker = None
        self.time_now: datetime = None
        self.data: pd.DataFrame = None
        
        
    def get_data(self, name: str, bars_ago: int = 0) -> any:
        """
        Get a single cell of data from `Strategy.data` DataFrame at the current
        backtest time, or a specified number of "bars ago".

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
        #idx = self.data.index.get_loc(self.time_now) - bars_ago
        idx = self.data.index.get_loc(self.time_now) - bars_ago
        return self.data.iloc[idx][name]


    def pre_start(self) -> None:
        """
        Called before the `Strategy` is started, and is used to set up any 
        necessary data or objects before the start of the session when the 
        strategy is run with the `IBLiveTradeEngine`.
        """
        pass


    def on_start(self) -> None:
        """
        Called once at the very beginning of a live trade session or backtest.
        """
        pass


    async def tick(self):
        """
        The `Strategy.tick()` method is where a user will define the basic logic 
        that runs a particular strategy.  The `tick()` method is called exactly 
        once per timestep in a backtest, and is where the `Strategy` may
        interact with an `Account` to submit orders based on current market 
        conditions.
        """
        pass
    
    
    async def post_tick(self):
        """
        Called after tick is called when the strategy is run with the 
        `IBLiveTradeEngine`.  This is where actions such as updating live 
        charts should occur.
        """
        pass
        
        
    def on_finish(self) -> None:
        """
        Called when a `Strategy` has finished, at the end of the backtest.
        This function can be used for saving-off any data collected during the 
        running of the backtest.
        """
        pass
    