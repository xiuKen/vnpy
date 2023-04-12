from datetime import datetime
from vnpy.trader.utility import BarGenerator, ArrayManager

from vnpy_spreadtrading import (
    SpreadStrategyTemplate,
    SpreadAlgoTemplate,
    SpreadData,
    OrderData,
    TradeData,
    TickData,
    BarData
)


class BasicSpreadBarStrategy(SpreadStrategyTemplate):
    """"""

    author = "kun.qian"

    buy_price = 0.0
    sell_price = 0.0
    cover_price = 0.0
    short_price = 0.0
    max_pos = 0.0
    payup = 10
    interval = 5
    start_time = "9:00:00"
    end_time = "15:00:00"

    spread_pos = 0.0
    update_time = None

    parameters = [
        "buy_price",
        "sell_price",
        "cover_price",
        "short_price",
        "max_pos",
        "payup",
        "interval"
    ]
    variables = [
        "spread_pos",
        "update_time"
    ]

    def __init__(
        self,
        strategy_engine,
        strategy_name: str,
        spread: SpreadData,
        setting: dict
    ):
        """"""
        super().__init__(
            strategy_engine, strategy_name, spread, setting
        )

        self.start_t = datetime.strptime(self.start_time, "%H:%M:%S").time()
        self.end_t = datetime.strptime(self.end_time, "%H:%M:%S").time()

        self.bg = BarGenerator(self.on_spread_bar)
        self.am = ArrayManager()

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")
        
        self.load_bar(10)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

        self.update_time = None
        self.buy_algoid = ""
        self.sell_algoid = ""
        self.short_algoid = ""
        self.cover_algoid = ""
        self.put_event()

    def on_spread_data(self):
        """
        Callback when spread price is updated.
        """
        print("on_spread_data")
        tick = self.get_spread_tick()
        self.on_spread_tick(tick)

    def on_spread_tick(self, tick: TickData):
        """
        Callback when new spread tick data is generated.
        """
        self.bg.update_tick(tick)

    def on_spread_bar(self, bar: BarData):
        """
        Callback when spread bar data is generated.
        """
        # Trading is only allowed within given start/end time range
        # self.update_time = self.spread.datetime.time()
        # if self.update_time < self.start_t or self.update_time >= self.end_t:
        #     self.stop_open_algos()
        #     self.stop_close_algos()
        #     self.put_event()
        #     return
        
        self.stop_all_algos()

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        if not self.spread_pos:
            if bar.close_price >= self.short_price:
                self.start_short_algo(
                    self.short_price,
                    self.max_pos,
                    payup=self.payup,
                    interval=self.interval
                )
            elif bar.close_price <= self.buy_price:
                self.start_long_algo(
                    self.buy_price,
                    self.max_pos,
                    payup=self.payup,
                    interval=self.interval
                )
        elif self.spread_pos < 0:
            if bar.close_price <= self.cover_price:
                self.start_long_algo(
                    self.cover_price,
                    abs(self.spread_pos),
                    payup=self.payup,
                    interval=self.interval
                )
        elif self.spread_pos > 0:
            if bar.close_price >= self.sell_price:
                self.start_short_algo(
                    self.sell_price,
                    abs(self.spread_pos),
                    payup=self.payup,
                    interval=self.interval
                )

        self.put_event()

    def on_spread_pos(self):
        """
        Callback when spread position is updated.
        """
        self.spread_pos = self.get_spread_pos()
        self.put_event()

    def on_spread_algo(self, algo: SpreadAlgoTemplate):
        """
        Callback when algo status is updated.
        """
        pass

    def on_order(self, order: OrderData):
        """
        Callback when order status is updated.
        """
        print("on_order")
        pass

    def on_trade(self, trade: TradeData):
        """
        Callback when new trade data is received.
        """
        pass

    def stop_open_algos(self):
        """"""
        if self.buy_algoid:
            self.stop_algo(self.buy_algoid)

        if self.short_algoid:
            self.stop_algo(self.short_algoid)

    def stop_close_algos(self):
        """"""
        if self.sell_algoid:
            self.stop_algo(self.sell_algoid)

        if self.cover_algoid:
            self.stop_algo(self.cover_algoid)
