import os 
from ib_async_trader import *

TESTS_PATH = os.path.dirname(os.path.realpath(__file__))


class MyStrat(Strategy):
    
    def __init__(self, underlying_contract: ib.Contract):
        super().__init__(underlying_contract)
        
        
    async def tick(self):
        t = self.time_now
        o = self.get_data("open")
        h = self.get_data("high")
        l = self.get_data("low")
        c = self.get_data("close")
        print(f"{t} | ${o:.2f} ${h:.2f} ${l:.2f} ${c:.2f}")
        

def test_backtest_engine():
    contract = ib.Future(symbol="ES", 
                    lastTradeDateOrContractMonth="202412", 
                    exchange="CME", multiplier=50)

    strat = MyStrat(contract)
    data = pd.read_csv(f"{TESTS_PATH}/sample_es_data.csv", index_col="date", 
                       parse_dates=["date"])
    engine = BacktestEngine(strat, data)
    engine.run()
