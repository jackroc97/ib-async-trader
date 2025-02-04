from .data import Data
from .strategy import Strategy


class Engine:
    
    def __init__(self, strategy: Strategy, datas: dict[str, Data]):
        self.strategy = strategy
        self.datas = datas
        self.strategy.datas = datas
    
    
    def run(self) -> None:
        pass
