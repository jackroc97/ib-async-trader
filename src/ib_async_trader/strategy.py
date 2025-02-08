import pandas as pd

from datetime import datetime

from .broker import Broker
from .data import Data


class Strategy:
    """
    The `Strategy` class is an abstract class that is designed to provided a 
    basic framework for making custom strategies to be run in a backtest.  A 
    user's custom strategies should inherit from this class and implement its
    methods.
    """
    
    def __init__(self):
        """Initialize a `Strategy` object."""
        self.broker: Broker = None
        self.time_now: datetime = None
        self.datas: dict[str, Data]
        

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
        
        
    def on_finish(self) -> None:
        """
        Called when a `Strategy` has finished, at the end of the backtest.
        This function can be used for saving-off any data collected during the 
        running of the backtest.
        """
        pass
    
    
    def on_new_data(data_id: str, df: pd.DataFrame, update_num: int):
        pass