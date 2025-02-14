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
        

    async def tick(self) -> None:
        """
        The `Strategy.tick()` method is where a user will define the basic logic 
        that runs a particular strategy.  The `tick()` method is called exactly 
        once per timestep in a backtest, and is where the `Strategy` may
        interact with an `Account` to submit orders based on current market 
        conditions.
        """
        pass
        
        
    def on_data_update(self, data_id: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        This will be called whenever data is updated.  For backtesting, it is
        called once at the beginning of the backtest, to improve performance.
        For live trades it is called whenever new data is available.

        The idea is that this will be used to perform any analysis or 
        calculations on the data that are needed for the strategy.

        Args:
            data_id (str): The ID for the data that has been udpated (since 
                strategies can have multiple datas that they read from).
            df (pd.DataFrame): The updated data.
        """
        return df
        
        
    def on_finish(self) -> None:
        """
        Called when a `Strategy` has finished, at the end of the backtest.
        This function can be used for saving-off any data collected during the 
        running of the backtest.
        """
        pass
    