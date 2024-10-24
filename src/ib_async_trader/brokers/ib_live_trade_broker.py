import ib_async as ib

from ..broker import Broker


class IBLiveTradeBroker(Broker):
    
    def __init__(self, ib: ib.IB):
        super().__init__()
        self.ib = ib
            
            
    def get_account_values(self) -> list[ib.AccountValue]:
        return self.ib.accountValues()
    
            
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
    
    
    def place_order(self, contract: ib.Contract, order: ib.Order,
                    status_event: callable = None, modify_event: callable = None,
                    fill_event: callable = None, commissionReportEvent: callable = None,
                    filled_event: callable = None, cancel_event: callable = None,
                    cancelled_event: callable = None) -> ib.Trade:
        trade = self.ib.placeOrder(contract, order)
        if status_event: trade.statusEvent += status_event
        if modify_event: trade.modifyEvent += modify_event
        if fill_event: trade.fillEvent += fill_event
        if commissionReportEvent: trade.commissionReportEvent += commissionReportEvent
        if filled_event: trade.filledEvent += filled_event
        if cancel_event: trade.cancelEvent += cancel_event
        if cancelled_event: trade.cancelledEvent += cancelled_event
        return trade
    