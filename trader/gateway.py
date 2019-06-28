# coding=utf-8
from abc import abstractmethod

from event.engine import EventEngine, Event
from trader.event import EVENT_TICK, EVENT_TRADE, EVENT_ORDER, EVENT_ACCOUNT, EVENT_POSITION, EVENT_LOG, EVENT_CONTRACT, \
    EVENT_BAR
from trader.object import KLineRequest, BarData, TickData, TradeData, OrderData, PositionData, LogData, AccountData, \
    ContractData, CancelRequest, OrderRequest, SubscribeRequest, SubscribeBarRequest

from typing import List, Any, Sequence

__author__ = "hanweiwei"
__date__ = "2019-05-31"


class BaseGateway(object):

    def __init__(self, event_engine: EventEngine, gateway_name: str):
        """"""
        self.event_engine = event_engine
        self.gateway_name = gateway_name

    @abstractmethod
    def get_kline_data(self, kline_request: KLineRequest):
        """

        :param kline_request:
        :type kline_request:KLineRequest
        :rtype: List[BarData]
        :return:

        """
        raise NotImplementedError

    def on_event(self, type: str, data: Any = None):
        """
        General event push.
        """
        event = Event(type, data)
        self.event_engine.put(event)

    def on_bar(self, bar: BarData):
        """
        bar event push.
        bar event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_BAR, bar)
        self.on_event(EVENT_BAR + bar.vt_symbol, bar)

    def on_tick(self, tick: TickData):
        """
        Tick event push.
        Tick event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_TICK, tick)
        self.on_event(EVENT_TICK + tick.vt_symbol, tick)

    def on_trade(self, trade: TradeData):
        """
        Trade event push.
        Trade event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_TRADE, trade)
        self.on_event(EVENT_TRADE + trade.vt_symbol, trade)

    def on_order(self, order: OrderData):
        """
        Order event push.
        Order event of a specific vt_orderid is also pushed.
        """
        self.on_event(EVENT_ORDER, order)
        self.on_event(EVENT_ORDER + order.vt_orderid, order)

    def on_position(self, position: PositionData):
        """
        Position event push.
        Position event of a specific vt_symbol is also pushed.
        """
        self.on_event(EVENT_POSITION, position)
        self.on_event(EVENT_POSITION + position.vt_symbol, position)

    def on_account(self, account: AccountData):
        """
        Account event push.
        Account event of a specific vt_accountid is also pushed.
        """
        self.on_event(EVENT_ACCOUNT, account)
        self.on_event(EVENT_ACCOUNT + account.vt_accountid, account)

    def on_log(self, log: LogData):
        """
        Log event push.
        """
        self.on_event(EVENT_LOG, log)

    def on_contract(self, contract: ContractData):
        """
        Contract event push.
        """
        self.on_event(EVENT_CONTRACT, contract)

    @abstractmethod
    def connect(self, setting: dict):
        """
        Start gateway connection.
        to implement this method, you must:
        * connect to server if necessary
        * log connected if all necessary connection is established
        * do the following query and response corresponding on_xxxx and write_log
            * contracts : on_contract
            * account asset : on_account
            * account holding: on_position
            * orders of account: on_order
            * trades of account: on_trade
        * if any of query above is failed,  write log.
        future plan:
        response callback/change status instead of write_log
        """
        pass

    @abstractmethod
    def close(self):
        """
        Close gateway connection.
        """
        pass

    @abstractmethod
    def subscribe(self, req: SubscribeRequest):
        """
        Subscribe tick data update.
        """
        pass

    @abstractmethod
    def subscribe_bar(self, req: SubscribeBarRequest):
        """
        Subscribe bar data update.
        """
        pass

    @abstractmethod
    def send_order(self, req: OrderRequest) -> str:
        """
        Send a new order to server.
        implementation should finish the tasks blow:
        * create an OrderData from req using OrderRequest.create_order_data
        * assign a unique(gateway instance scope) id to OrderData.orderid
        * send request to server
            * if request is sent, OrderData.status should be set to Status.SUBMITTING
            * if request is failed to sent, OrderData.status should be set to Status.REJECTED
        * response on_order:
        * return OrderData.vt_orderid
        :return str vt_orderid for created OrderData
        """
        pass

    @abstractmethod
    def cancel_order(self, req: CancelRequest):
        """
        Cancel an existing order.
        implementation should finish the tasks blow:
        * send request to server
        """
        pass

    def send_orders(self, reqs: Sequence[OrderRequest]):
        """
        Send a batch of orders to server.
        Use a for loop of send_order function by default.
        Reimplement this function if batch order supported on server.
        """
        vt_orderids = []

        for req in reqs:
            vt_orderid = self.send_order(req)
            vt_orderids.append(vt_orderid)

        return vt_orderids

    def cancel_orders(self, reqs: Sequence[CancelRequest]):
        """
        Cancel a batch of orders to server.
        Use a for loop of cancel_order function by default.
        Reimplement this function if batch cancel supported on server.
        """
        for req in reqs:
            self.cancel_order(req)

    @abstractmethod
    def query_account(self):
        """
        Query account balance.
        """
        pass

    @abstractmethod
    def query_position(self):
        """
        Query holding positions.
        """
        pass

    # def query_history(self, req: HistoryRequest):
    #     """
    #     Query bar history data.
    #     """
    #     pass

    def get_default_setting(self):
        """
        Return default setting dict.
        """
        return self.default_setting