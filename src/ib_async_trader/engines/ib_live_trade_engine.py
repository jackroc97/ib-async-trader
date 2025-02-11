import ib_async as ib
import sys
import traceback

from datetime import datetime, timedelta

from ..brokers.ib_live_trade_broker import IBLiveTradeBroker
from ..datas.data_stream import DataStream
from ..engine import Engine
from ..strategy import Strategy


class IBLiveTradeEngine(Engine):
    
    def __init__(self, strategy: Strategy, datas: dict[str, DataStream], 
                 tick_rate_s: float = 1, host: str="127.0.0.1", port: int=7496, 
                 client_id: int=1):
        super().__init__(strategy, datas)
        self.tick_rate_s = tick_rate_s
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = ib.IB()
        self.strategy_started = False
                
        
    async def run(self) -> None:
        # Initialize the broker
        self.strategy.broker = IBLiveTradeBroker(self.ib)

        # Connect to IB
        await self.ib.connectAsync(self.host, self.port, self.client_id)

        # Initialize the data streams
        data: DataStream
        for _, data in self.strategy.datas.items():
            await data.initialize(self.ib, self.strategy.on_data_update)

        # Call strategy on_start
        self.strategy.on_start()
        self.strategy_started = True
                
        # Schedule the tick event at the requested interval
        start_time = datetime.now()
        end_time = start_time + timedelta(days=1)
        time_range = ib.util.timeRangeAsync(start_time, 
                                            end_time, 
                                            self.tick_rate_s)
        
        try:
            # Call strategy tick function at each interval
            async for t in time_range:    
                self.strategy.time_now = t            
                await self.strategy.tick()
                
        except KeyboardInterrupt:
            print("\nStop requested by user.")
        
        except Exception as e:
            traceback.print_exception(e)
        
        finally:
            self.stop()
    
    
    def stop(self) -> None:
        if self.strategy_started:
            self.strategy.on_finish()
            
        self.ib.disconnect()
        sys.exit()
        