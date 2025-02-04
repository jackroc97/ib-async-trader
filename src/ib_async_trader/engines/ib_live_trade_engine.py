import asyncio
import ib_async as ib
import sys

from ..brokers.ib_live_trade_broker import IBLiveTradeBroker
from ..datas.data_stream import DataStream
from ..engine import Engine
from ..strategy import Strategy


class IBLiveTradeEngine(Engine):
    
    def __init__(self, strategy: Strategy, datas: dict[str, DataStream], 
                 tick_rate_s: int = 1, host: str="127.0.0.1", port: int=7496, 
                 client_id: int=1):
        super().__init__(strategy, datas)
        self.tick_rate_s = tick_rate_s
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = ib.IB()
                
    
    def run(self) -> None:
                
        try:
            # Initialize the broker
            self.strategy.broker = IBLiveTradeBroker(self.ib)

            # Connect to IB
            self.ib.connect(self.host, self.port, self.client_id)

            # Initialize the data streams
            data: DataStream
            for data in self.strategy.datas:
                data.initialize(self.ib)

            # Call strategy on_start
            self.strategy.on_start()
                
            # Keep the process alive until a stop is requested by keypress
            while True:
                asyncio.run(self.strategy.tick())
                asyncio.run(self.strategy.post_tick())
                self.ib.sleep(self.tick_rate_s)
        
        except KeyboardInterrupt:
            self.stop()
        
        finally:
            self.stop()
        
        
    def stop(self) -> None:
        self.strategy.on_finish()
        self.ib.disconnect()
        sys.exit()
        