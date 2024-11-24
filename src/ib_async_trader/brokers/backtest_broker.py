import ib_async as ib
import pandas as pd

from datetime import datetime, timedelta

from ..broker import Broker
from ..utils.black_scholes import BlackScholes


class BacktestBroker(Broker):
    
    def __init__(self, starting_balance: float):
        super().__init__()
        self.open_trades: list[ib.Trade] = []
        self.open_positions: list[ib.Position] = []
        
        self.cash_balance = starting_balance        
        self.account_pnl = ib.PnL()
        
        
    def initialize(self, start_time):
        self.time_now = start_time
    

    def update(self, time_now: datetime, last_data: pd.Series):
        self.time_now = time_now
        self.last_data = last_data
        self._handle_contract_expiry()        
        self._handle_open_trades()


    def get_buying_power(self) -> float:
        return self.cash_balance
    
    
    def get_cash_balance(self) -> float:
        return self.cash_balance


    def get_account_values(self) -> list[ib.AccountValue]:
        return None
    

    def get_positions(self) -> list[ib.Position]:
        return self.open_positions
    
            
    async def get_all_positions(self) -> list[ib.Position]:
        return self.open_positions
    
    
    def get_open_orders(self) -> list[ib.Order]:
        return [t.order for t in self.open_trades]
            
            
    def get_open_trades(self) -> list[ib.Trade]:
        return self.open_trades
            
            
    async def get_all_open_trades(self) -> list[ib.Trade]:
        return self.open_trades
    
    
    async def get_options_chain(self, underlying: ib.Contract) -> list[ib.OptionChain]:
        expirations = [(self.time_now + timedelta(days=x)).strftime("%Y%m%d") \
            for x in range(30)]
        atm_strk = int(5 * round(self.last_data["close"] / 5))
        strikes = [strk for strk in range(atm_strk - 100, atm_strk + 100, 5)]
        return [ib.OptionChain(underlying.exchange, underlying.conId, 
                               underlying.tradingClass, underlying.multiplier, 
                               expirations, strikes)]


    async def qualify_contracts(self, *contracts: ib.Contract) -> list[ib.Contract]:
        for contract in contracts:
            if not contract.localSymbol:
                contract.localSymbol = f"{contract.symbol}{contract.lastTradeDateOrContractMonth}{contract.right}{contract.strike}"
        return contracts
    
    
    async def what_if_order(self, contract: ib.Contract, order: ib.Order) -> ib.OrderState:
        # TODO: To be more realistic, this should return an OrderStat object
        # that reflects what would happen if the order was submitted (effects
        # on margin, etc.)
        state = ib.OrderState()
        return state
    
    
    def place_order(self, contract: ib.Contract, order: ib.Order, 
                    status_event: callable = None, modify_event: callable = None,
                    fill_event: callable = None, commissionReportEvent: callable = None,
                    filled_event: callable = None, cancel_event: callable = None,
                    cancelled_event: callable = None) -> ib.Trade:

        status=ib.OrderStatus()
        trade = ib.Trade(contract=contract, order=order, orderStatus=status)
        if status_event: trade.statusEvent += status_event
        if modify_event: trade.modifyEvent += modify_event
        if fill_event: trade.fillEvent += fill_event
        if commissionReportEvent: trade.commissionReportEvent += commissionReportEvent
        if filled_event: trade.filledEvent += filled_event
        if cancel_event: trade.cancelEvent += cancel_event
        if cancelled_event: trade.cancelledEvent += cancelled_event
        self.open_trades.append(trade)
        
        trade.log.append(ib.TradeLogEntry(self.time_now, status="Submitted"))
        trade.statusEvent(trade)
        return trade
            
    
    def _get_contract_expiration_dt(self, contract: ib.Contract) -> datetime:
        return datetime.strptime(contract.lastTradeDateOrContractMonth, 
                                 "%Y%m%d").replace(hour=15, 
                                                   minute=59, 
                                                   second=59, 
                                                   microsecond=0,
                                                   tzinfo=self.time_now.tzinfo)


    def _is_contract_expired(self, contract: ib.Contract) -> bool:
        return self.time_now >= self._get_contract_expiration_dt(contract)
        
        
    def _handle_contract_expiry(self):
        for pos in self.open_positions:
            if self._is_contract_expired(pos.contract):
                
                # If a position is expired, place a closing order for it to 
                # simulate expiration.  This assumes that positions are not 
                # assigned, but rather all contracts settle to cash.
                action = "SELL" if pos.position > 0 else "BUY"
                closing_ord = ib.MarketOrder(action, pos.position)
                closing_trade = ib.Trade(pos.contract, closing_ord)
                self._execute_trade(closing_trade)
        
        
    def _get_trade_cash_effect(self, trade: ib.Trade) -> float:
        coeff = -1 if trade.order.action == "BUY" else 1
        if type(trade.contract) in [ib.Option, ib.FuturesOption]:
            
            exp_dt = self._get_contract_expiration_dt(trade.contract)
            
            # Get the time to expiration (t) and the theoretical call or put 
            # price (c, p)
            t = BlackScholes.time_to_expiration_years(exp_dt, self.time_now)
        
            # To avoid a division by zero error, never let t reach exactly 0...
            # just set it to a "sufficiently small" number.
            # NOTE: This will generate "bogus" values for option prices after 
            # they have expired, since the price of the underlying will continue
            # to move but time to expiration has been frozen.
            if t <= 0:
                t = 1E-12

            c, p = BlackScholes.call_put_price(self.last_data["close"],
                                                trade.contract.strike, 
                                                t, self.last_data["iv"])    
            price = c if trade.contract.right in ["CALL", "C"] else p
        else:
            price = self.last_data["close"]
            
        return coeff * trade.order.totalQuantity * trade.contract.multiplier \
            * price
        
        
    def _can_execute_trade(self, trade: ib.Trade) -> bool:
        
        # Is the contract still valid (i.e., not expired)?
        is_valid = not self._is_contract_expired(trade.contract)
        
        # Do we have enough cash or margin to execute this trade?
        cash_eff = self._get_trade_cash_effect(trade)
        
        return is_valid and (self.cash_balance + cash_eff) > 0

    
    def _update_positions(self, new_position: ib.Position) -> bool:
        
        for old_position in self.open_positions:
            if old_position.contract == new_position.contract:
                new_qty = old_position.position + new_position.position
                if new_qty > 0:
                    new_avg_cost = ((old_position.avgCost + 
                                     new_position.avgCost) / new_qty)
                else: 
                    new_avg_cost = old_position.avgCost
                    
                new_position = ib.Position("", new_position.contract, 
                                           new_qty, new_avg_cost)
                self.open_positions.remove(old_position)
                
        if new_position.position > 0:
            self.open_positions.append(new_position)    
        
    
    def _execute_trade(self, trade: ib.Trade):
        """
        Execute a `Trade` by converting it into a `Position` and updating the
        account balance.

        Args:
            trade (ib.Trade): The `Trade` to execute.
        """
        
        # Determine what effect this trade will have on account balance
        cash_eff = self._get_trade_cash_effect(trade)
        
        # Create the resulting position
        coeff = 1 if trade.order.action == "BUY" else -1
        qty = coeff * trade.order.totalQuantity 
        avg_cost = abs(cash_eff) / qty
        position = ib.Position("", trade.contract, qty, avg_cost)
        
        # Update open_positions, and remove this from open_orders
        self._update_positions(position)
        
        # Update the balance on the account
        self.cash_balance += cash_eff
        
        self.account_pnl.realizedPnL += cash_eff

        # Create execution on commission data, then call trade fill events
        # NOTE: This currently assumes perfect execution of the entire order
        # all at once (one fill for all shares) and no commissions.
        # TODO: Could potentially model commisssions and imperfect executions
        # here.
        # NOTE: IB api convention is that the fill price is is per contract,
        # so here we must divide by the contract multiplier.
        exec_price = abs(avg_cost)/trade.contract.multiplier
        exec = ib.Execution(time=self.time_now, 
                            exchange=trade.contract.exchange, 
                            shares=qty, 
                            price=exec_price, 
                            cumQty=qty, 
                            avgPrice=exec_price)
        comm = ib.CommissionReport()
        fill = ib.Fill(trade.contract, exec, comm, self.time_now)
        trade.fills.append(fill)
        
        trade.log.append(
            ib.TradeLogEntry(self.time_now, 
                             status="Submitted", 
                             message=f"Fill {trade.order.totalQuantity:.1f}\@{exec_price:.2f}"))
        trade.log.append(ib.TradeLogEntry(self.time_now, status="Filled"))
        trade.statusEvent(trade)
        
        trade.fillEvent(trade, fill)
        trade.filledEvent(trade)
        trade.commissionReportEvent(trade, fill, comm)
        
    
    def _cancel_trade(self, trade: ib.Trade):
        """
        Remove the (`Contract`, `Order`) tuple from `open_orders`, then call
        the cancel events on the `Trade`.

        Args:
            trade (ib.Trade): The `Trade` to cancel.
        """
        trade.log.append(ib.TradeLogEntry(self.time_now, status="Cancelled"))
        trade.cancelEvent(trade)
        trade.cancelledEvent(trade)
        trade.statusEvent(trade)
        

    def _handle_open_trades(self):
        
        for i, trade in enumerate(self.open_trades):
            
            if self._can_execute_trade(trade):
                self._execute_trade(trade)
                del self.open_trades[i]
            else:
                self._cancel_trade(trade)
                del self.open_trades[i]
