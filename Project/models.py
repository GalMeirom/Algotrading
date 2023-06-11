from abc import ABCMeta, abstractmethod
import pandas as pd
from enum import Enum

class Sector(Enum):
    ENERGY = 1
    REAL_ESTATE = 2
    CONSUMER_CYCLICAL = 3

    def __str__(self) -> str:
        if self.value == 1:
            return "Energy"
        if self.value == 2:
            return "Real Estate"
        if self.value == 3:
            return "Consumer Cyclical"
    

class OrderType(Enum):
    OPEN_LONG = 1
    OPEN_SHORT = 2
    CLOSE_LONG = 3
    CLOSE_SHORT = 4



class PositionSide(Enum):
    LONG = 1
    SHORT = 2


class BrokerInstruction:
    def __init__(self, order_type: OrderType, price: float, sector:Sector):
        self.order_type = order_type
        self.price = price
        self.sector = sector


class Position:
    def __init__(self, qty: float, price: float, side: PositionSide, sector:Sector):
        self.qty = qty
        self.price = price
        self.side = side
        self.low = price
        self.high = price
        self.sector = sector


class Strategy(metaclass=ABCMeta):
    @abstractmethod
    def enter_position(self, data: pd.DataFrame) -> BrokerInstruction:
        raise NotImplementedError

    @abstractmethod
    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        raise NotImplementedError


class OutOfMoneyException(Exception):
    pass
