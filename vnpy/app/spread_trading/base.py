from typing import Dict, List
from math import floor, ceil
from datetime import datetime

from vnpy.trader.object import TickData, PositionData, TradeData
from vnpy.trader.constant import Direction, Offset, Exchange


EVENT_SPREAD_DATA = "eSpreadData"
EVENT_SPREAD_POS = "eSpreadPos"
EVENT_SPREAD_LOG = "eSpreadLog"
EVENT_SPREAD_ALGO = "eSpreadAlgo"
EVENT_SPREAD_STRATEGY = "eSpreadStrategy"


class LegData:
    """"""

    def __init__(self, vt_symbol: str):
        """"""
        self.vt_symbol: str = vt_symbol

        # Price and position data
        self.bid_price: float = 0
        self.ask_price: float = 0
        self.bid_volume: float = 0
        self.ask_volume: float = 0

        self.long_pos: float = 0
        self.short_pos: float = 0
        self.net_pos: float = 0

        # Tick data buf
        self.tick: TickData = None

    def update_tick(self, tick: TickData):
        """"""
        self.bid_price = tick.bid_price_1
        self.ask_price = tick.ask_price_1
        self.bid_volume = tick.bid_volume_1
        self.ask_volume = tick.ask_volume_1

        self.tick = tick

    def update_position(self, position: PositionData):
        """"""
        if position.direction == Direction.NET:
            self.net_pos = position.volume
        else:
            if position.direction == Direction.LONG:
                self.long_pos = position.volume
            else:
                self.short_pos = position.volume
            self.net_pos = self.long_pos - self.short_pos

    def update_trade(self, trade: TradeData):
        """"""
        if trade.direction == Direction.LONG:
            if trade.offset == Offset.OPEN:
                self.long_pos += trade.volume
            else:
                self.short_pos -= trade.volume
        else:
            if trade.offset == Offset.OPEN:
                self.short_pos += trade.volume
            else:
                self.long_pos -= trade.volume

        self.net_pos = self.long_pos - self.net_pos


class SpreadData:
    """"""

    def __init__(
        self,
        name: str,
        legs: List[LegData],
        price_multipliers: Dict[str, int],
        trading_multipliers: Dict[str, int],
        active_symbol: str
    ):
        """"""
        self.name: str = name

        self.legs: Dict[str, LegData] = {}
        self.active_leg: LegData = None
        self.passive_legs: List[LegData] = []

        # For calculating spread price
        self.price_multipliers: Dict[str: int] = price_multipliers

        # For calculating spread pos and sending orders
        self.trading_multipliers: Dict[str: int] = trading_multipliers

        self.price_formula: str = ""
        self.trading_formula: str = ""

        for leg in legs:
            self.legs[leg.vt_symbol] = leg
            if leg.vt_symbol == active_symbol:
                self.active_leg = leg
            else:
                self.passive_legs.append(leg)

            price_multiplier = self.price_multipliers[leg.vt_symbol]
            if price_multiplier > 0:
                self.price_formula += f"+{price_multiplier}*{leg.vt_symbol}"
            else:
                self.price_formula += f"{price_multiplier}*{leg.vt_symbol}"

            trading_multiplier = self.trading_multipliers[leg.vt_symbol]
            if trading_multiplier > 0:
                self.trading_formula += f"+{trading_multiplier}*{leg.vt_symbol}"
            else:
                self.trading_formula += f"{trading_multiplier}*{leg.vt_symbol}"

        # Spread data
        self.bid_price: float = 0
        self.ask_price: float = 0
        self.bid_volume: float = 0
        self.ask_volume: float = 0

        self.net_pos: float = 0
        self.datetime: datetime = None

    def calculate_price(self):
        """"""
        self.clear_price()

        # Go through all legs to calculate price
        for n, leg in enumerate(self.legs.values()):
            # Filter not all leg price data has been received
            if not leg.bid_volume or not leg.ask_volume:
                self.clear_price()
                return

            # Calculate price
            price_multiplier = self.price_multipliers[leg.vt_symbol]
            if price_multiplier > 0:
                self.bid_price += leg.bid_price * price_multiplier
                self.ask_price += leg.ask_price * price_multiplier
            else:
                self.bid_price += leg.ask_price * price_multiplier
                self.ask_price += leg.bid_price * price_multiplier

            # Calculate volume
            trading_multiplier = self.trading_multipliers[leg.vt_symbol]

            if trading_multiplier > 0:
                adjusted_bid_volume = floor(
                    leg.bid_volume / trading_multiplier)
                adjusted_ask_volume = floor(
                    leg.ask_volume / trading_multiplier)
            else:
                adjusted_bid_volume = floor(
                    leg.ask_volume / abs(trading_multiplier))
                adjusted_ask_volume = floor(
                    leg.bid_volume / abs(trading_multiplier))

            # For the first leg, just initialize
            if not n:
                self.bid_volume = adjusted_bid_volume
                self.ask_volume = adjusted_ask_volume
            # For following legs, use min value of each leg quoting volume
            else:
                self.bid_volume = min(self.bid_volume, adjusted_bid_volume)
                self.ask_volume = min(self.ask_volume, adjusted_ask_volume)

            # Update calculate time
            self.datetime = datetime.now()

    def calculate_pos(self):
        """"""
        self.net_pos = 0

        for n, leg in enumerate(self.legs.values()):
            trading_multiplier = self.trading_multipliers[leg.vt_symbol]
            adjusted_net_pos = leg.net_pos / trading_multiplier

            if adjusted_net_pos > 0:
                adjusted_net_pos = floor(adjusted_net_pos)
            else:
                adjusted_net_pos = ceil(adjusted_net_pos)

            if not n:
                self.net_pos = adjusted_net_pos
            else:
                if adjusted_net_pos > 0:
                    self.net_pos = min(self.net_pos, adjusted_net_pos)
                else:
                    self.net_pos = max(self.net_pos, adjusted_net_pos)

    def clear_price(self):
        """"""
        self.bid_price = 0
        self.ask_price = 0
        self.bid_volume = 0
        self.ask_volume = 0

    def calculate_leg_volume(self, vt_symbol: str, spread_volume: float) -> float:
        """"""
        leg = self.legs[vt_symbol]
        trading_multiplier = self.trading_multipliers[leg.vt_symbol]
        leg_volume = spread_volume * trading_multiplier
        return leg_volume

    def calculate_spread_volume(self, vt_symbol: str, leg_volume: float) -> float:
        """"""
        leg = self.legs[vt_symbol]
        trading_multiplier = self.trading_multipliers[leg.vt_symbol]
        spread_volume = leg_volume / trading_multiplier

        if spread_volume > 0:
            spread_volume = floor(spread_volume)
        else:
            spread_volume = ceil(spread_volume)

        return spread_volume

    def to_tick(self):
        """"""
        tick = TickData(
            symbol=self.name,
            exchange=Exchange.LOCAL,
            datetime=self.datetime,
            name=self.name,
            last_price=(self.bid_price + self.ask_price) / 2,
            bid_price_1=self.bid_price,
            ask_price_1=self.ask_price,
            bid_volume_1=self.bid_volume,
            ask_volume_1=self.ask_volume,
            gateway_name="SPREAD"
        )
        return tick
