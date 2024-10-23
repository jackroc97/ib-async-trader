import ib_async as ib

from ..broker import Broker


class IBLiveTradeBroker(Broker):
    
    def __init__(self, ib: ib.IB):
        super().__init__()
        self.ib = ib
            
            
    def get_positions(self) -> list[ib.Position]:
        return self.ib.positions()
    
            
    async def get_all_positions(self) -> list[ib.Position]:
        return await self.ib.reqPositionsAsync()
    
    
    def get_open_orders(self) -> list[ib.Order]:
        return self.ib.openOrders()
            
            
    def get_open_trades(self) -> list[ib.Trade]:
        return self.ib.openTrades()
            
            
    async def get_all_open_trades(self) -> list[ib.Trade]:
        return await self.ib.reqAllOpenOrdersAsync()
    
    
    async def get_options_chain(self, underlying: ib.Contract) -> list[ib.OptionChain]:
        return await self.ib.reqSecDefOptParamsAsync(underlying.symbol, underlying.exchange, underlying.secType, underlying.conId)
        
    
    async def qualify_contracts(self, *contracts: ib.Contract) -> list[ib.Contract]:
        return await self.ib.qualifyContractsAsync(*contracts)
    
    
    async def what_if_order(self, contract: ib.Contract, order: ib.Order) -> ib.OrderState:
        return await self.ib.whatIfOrderAsync(contract, order)
    
    
    def place_order(self, contract: ib.Contract, order: ib.Order) -> ib.Trade:
        return self.ib.placeOrder(contract, order)
    