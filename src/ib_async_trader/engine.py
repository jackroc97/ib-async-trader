from .strategy import Strategy


class Engine:
    
    def __init__(self, strategy: Strategy):
        self.strategy = strategy
    
    
    def run(self) -> None:
        pass
