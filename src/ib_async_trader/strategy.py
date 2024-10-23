from datetime import datetime

import pandas as pd
import ib_async as ib
from lightweight_charts import Chart

from .broker import Broker
from .utils.chart_utils import ChartUtils


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
        self.chart: Chart = None
        
        
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
        loc = self.data.index.get_loc(self.time_now)
        idx = loc - bars_ago
        return self.data.iloc[idx][name]
        
        
    def barssince(self, conditional: callable, df: pd.DataFrame, offset: int = 0, 
                  max_bars: int = None) -> int:
        """
        Returns the number of bars of data in `df` since a condition given 
        in `conditional` was `True`.  Bars are counted backwards from the
        current bar (current time in backtest).

        Args:
            conditional (callable): A function representing the condition that 
                is being tested in the data.  The args of the function should 
                correspond to the columns of data being passed in `df`.
            df (pd.DataFrame): The data on which to test the condition.
            offset (int, optional): Offsets the current bar by the amount 
                specified.  Defaults to 0.
            max_bars (int, optional): Max number of bars to look back before
                returning None.  Highly recommended to set to non-zero to
                improve performance.  Defaults to None.

        Returns:
            int: The number of bars since the condition was True.
        """
        end_idx = (df.index.get_loc(self.time_now) + 1) - offset
        start_idx = end_idx - max_bars if max_bars else 0
        sliced = df.iloc[start_idx:end_idx].copy()        
        sliced["condition"] = sliced.apply(lambda row: conditional(*row.values), axis=1)
        t = sliced.where(sliced["condition"]).last_valid_index()
        return (end_idx - df.index.get_loc(t) - 1) if t else None
    
    
    def update_live_chart(self):
        """
        Performs live updates of the chart as the strategy is running.
        This function is only called if backtest chart options is set to
        `ChartOptions.LIVE_CHART`.
        """
        if self.chart and len(self.chart.data) < 1:
            ChartUtils.set_chart_data(self.chart, self.data[:self.time_now])
            self.chart.show()
        else:
            ChartUtils.update_chart(self.chart, self.data.loc[self.time_now])
            
    
    async def tick(self):
        """
        The `Strategy.tick()` method is where a user will define the basic logic 
        that runs a particular strategy.  The `tick()` method is called exactly 
        once per timestep in a backtest, and is where the `Strategy` may
        interact with an `Account` to submit orders based on current market 
        conditions.
        """
        pass
    
    
    def on_start(self) -> None:
        pass
    
        
    def on_finish(self) -> None:
        """
        Called when a `Strategy` has finished, at the end of the backtest.
        This function can be used for saving-off any data collected during the 
        running of the backtest.
        """
        pass
    