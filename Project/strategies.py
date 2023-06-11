from models import Strategy, BrokerInstruction, OrderType, PositionSide, Position, Sector
from abc import abstractmethod
import random
import pandas as pd

from utils import filter_by_sector


class RandomStrategy(Strategy):
    """
    Opens a position with probability buy_p, decides whether long or short with p = 0.5
    Closes position with probability sell_p
    """

    def __init__(self, buy_p=0.1, sell_p=0.005):
        super().__init__()
        self.buy_p = buy_p
        self.sell_p = sell_p

    def enter_position(self, data: pd.DataFrame) -> BrokerInstruction:
        last_close = data["Close"].iloc[-1]
        if self.buy_p > random.random():
            if random.random() >= 0.5:
                return BrokerInstruction(OrderType.OPEN_LONG, last_close)
            else:
                return BrokerInstruction(OrderType.OPEN_SHORT, last_close)

    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        last_close = data["Close"].iloc[-1]
        if self.sell_p > random.random():
            if position.side == PositionSide.LONG:
                return BrokerInstruction(OrderType.CLOSE_LONG, last_close)
            else:
                return BrokerInstruction(OrderType.CLOSE_SHORT, last_close)


class BuyAndHold(Strategy):
    def enter_position(self, data: pd.DataFrame):
        last_close = data["Close"].sum()
        return BrokerInstruction(OrderType.OPEN_LONG, last_close)

    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        return

class BuyAndHoldSector(BuyAndHold):
    def __init__(self, sector:Sector) -> None:
        super().__init__()
        self.sector = sector

    def enter_position(self, data: pd.DataFrame):
        last_close = data["Close"].sum()
        return BrokerInstruction(OrderType.OPEN_LONG, last_close, sector=self.sector)

    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        return


# Under the premice that only shorting evergy and long on commodities and real-estate
# 

class threshold_Sector(Strategy):
    
    def __init__(self, sector:Sector, inU:float, inD:float, outU:float, outD:float):
        super().__init__()
        self.sector = sector 
        self.thresh_inU = inU
        self.thresh_inD = inD
        self.thresh_outU = outU
        self.thresh_outD = outD
    
    @abstractmethod
    def enter_position(self, data: pd.DataFrame) -> BrokerInstruction:
        raise NotImplementedError

    @abstractmethod
    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        raise NotImplementedError
    

    def exit_position(
        self, data: pd.DataFrame, position: Position
    ) -> BrokerInstruction:
        return

class Energy_stratagy(threshold_Sector):
    
    def __init__(self, en_inU:float, en_inD:float,en_outU:float, en_outD:float):
        super().__init__(Sector.ENERGY, en_inU, en_inD, en_outU, en_outD)

    def act(self, data: pd.DataFrame, daily_grade:float) -> BrokerInstruction:
        last_close = data["Close"].sum()
        if daily_grade >= self.thresh_enter_short:
            return BrokerInstruction(OrderType.OPEN_LONG, last_close, self.sector)
        if daily_grade <= self.thresh_exit_short:
            return BrokerInstruction(OrderType.CLOSE_LONG, last_close, self.sector)
        else:
            return None

    def enter_position(self, data: pd.DataFrame, daily_grade:float) -> BrokerInstruction:
        last_close = data["Close"].sum()
        if (daily_grade >= self.thresh_inU) | (daily_grade <= self.thresh_inD):
            return BrokerInstruction(OrderType.OPEN_LONG, last_close, self.sector)
        else:
            return None

    def exit_position(self, data: pd.DataFrame, daily_grade:float) -> BrokerInstruction:
        last_close = data["Close"].sum()
        if (daily_grade < self.thresh_outU) & (daily_grade > self.thresh_outD):
            return BrokerInstruction(OrderType.CLOSE_LONG, last_close, self.sector)
        else:
            return None

class Neg_Sector_stratagy(threshold_Sector):
    
    def __init__(self,sector:Sector, inU:float, inD:float, outU:float, outD:float):
        super().__init__(sector, inU, inD, outU, outD)
    
    def act(self, data: pd.DataFrame, daily_grade:float) -> BrokerInstruction:
        last_close = data["Close"].sum()
        if daily_grade <= self.thresh_enter_long:
            return BrokerInstruction(OrderType.OPEN_SHORT, last_close, self.sector)
        if daily_grade >= self.thresh_exit_long:
            return BrokerInstruction(OrderType.CLOSE_SHORT, last_close, self.sector)
        else:
            return None

    def enter_position(self, data: pd.DataFrame, daily_grade:float) -> BrokerInstruction:
        last_close = data["Close"].sum()
        if (daily_grade >= self.thresh_inU) | (daily_grade <= self.thresh_inD):
            return BrokerInstruction(OrderType.OPEN_SHORT, last_close, self.sector)
        else:
            return None

    def exit_position(self, data: pd.DataFrame, daily_grade:float) -> BrokerInstruction:
        last_close = data["Close"].sum()
        if (daily_grade < self.thresh_outU) & (daily_grade > self.thresh_outD):
            return BrokerInstruction(OrderType.CLOSE_SHORT, last_close, self.sector)
        else:
            return None
        


class Weather():

    def __init__(self, en_inU:float, en_inD:float,en_outU:float, en_outD:float, re_inU:float, re_inD:float,re_outU:float, re_outD:float, cc_inU:float, cc_inD:float, cc_outU:float, cc_outD:float):
        super().__init__()
        self.strategies = [Energy_stratagy(en_inU, en_inD, en_outU, en_outD) ,Neg_Sector_stratagy(Sector.REAL_ESTATE,re_inU, re_inD, re_outU, re_outD ),Neg_Sector_stratagy(Sector.CONSUMER_CYCLICAL,cc_inU, cc_inD, cc_outU, cc_outD)]
    
    def get_actions(self, data:pd.DataFrame, daily_grade:float):
        actions = []
        for stra in self.strategies:
            data_by_sectors = filter_by_sector(data, stra.sector)
            actions.append(stra.act(data_by_sectors,daily_grade))
        return actions


class Weather_BH():
    def __init__(self):
        super().__init__()
        self.strategies = [BuyAndHoldSector(Sector.ENERGY) ,BuyAndHoldSector(Sector.REAL_ESTATE),BuyAndHoldSector(Sector.CONSUMER_CYCLICAL)]