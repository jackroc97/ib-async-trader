import ib_async as ib


class Broker:
    
    def __init__(self):
        pass
    
    
    def set_order_status_event(self, callback: callable) -> None:
        pass
    
    
    def get_buying_power(self) -> float:
        pass
    
    
    def get_cash_balance(self) -> float:
        pass
    
    
    def get_account_values(self) -> list[ib.AccountValue]:
        pass
    
    
    def get_positions(self) -> list[ib.Position]:
        pass
    
            
    async def get_all_positions(self) -> list[ib.Position]:
        pass
    
    
    def get_open_orders(self) -> list[ib.Order]:
        pass
            
            
    def get_open_trades(self) -> list[ib.Trade]:
        pass
            
            
    async def get_all_open_trades(self) -> list[ib.Trade]:
        pass
    
    
    async def get_options_chain(self, contract: ib.Contract) -> list[ib.OptionChain]:
        pass
    
    
    async def qualify_contracts(self, *contracts: ib.Contract) -> list[ib.Contract]:
        pass
    
    
    async def what_if_order(self, contract: ib.Contract, order: ib.Order) -> ib.OrderState:
        pass
    
    
    def place_order(self, contract: ib.Contract, order: ib.Order) -> ib.Trade:
        pass
    
     