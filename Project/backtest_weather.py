from typing import Dict
from models import (
    OutOfMoneyException,
    Strategy,
    BrokerInstruction,
    OrderType,
    PositionSide,
    Position,
    Sector

)
import math
import datetime
import pandas as pd
import numpy as np
from collections import defaultdict

from strategies import RandomStrategy, Neg_Sector_stratagy, Energy_stratagy, Weather
#from summary import Summary, plot_data
from utils import filter_by_sector, grade_daily, calculate_balance_type, update_balance, is_trading_day, grade_all_days, generate_relative_grade

POSITION_MARGIN = 500


class Backtest_weather:
    def __init__(
        self,
        strat_day: datetime.date,
        end_day: datetime.date,
        stocks_data: pd.DataFrame,
        weather_data: pd.DataFrame,
        commission: float,
        balance: int,
        en_inU:float,
        en_inD:float,
        en_outU:float,
        en_outD:float, 
        re_inU:float, 
        re_inD:float,
        re_outU:float, 
        re_outD:float, 
        cc_inU:float, 
        cc_inD:float, 
        cc_outU:float, 
        cc_outD:float,
        leverage: int = 1.0,
        window_size: int = 3,
        buy_percentage: float = 0.05,
    ):
    
        self.start_day = strat_day
        self.end_day= end_day
        # all the stocks data for the Half a year period
        self.stocks_data = stocks_data[(stocks_data['Date'] >= strat_day) & (stocks_data['Date'] < end_day)]
        # all the weather data for the Half a year period
        self.weather_data = weather_data[(weather_data['Date'] >= strat_day) & (weather_data['Date'] < end_day)]
        self.commission = commission
        self.balance = balance
        self.wallet = {"NIS": balance, "loaned_NIS": 0, "Energy_index": 0, "loaned_Energy_index": 0, "Real_Estate_index": 0, "loaned_Real_Estate_index":0, "Consumer_Cyclical_index": 0, "loaned_Consumer_Cyclical_index":0}
        self.strategy = Weather(en_inU, en_inD,en_outU, en_outD, re_inU, re_inD,re_outU, re_outD, cc_inU, cc_inD, cc_outU, cc_outD)
        self.leverage = leverage
        self.window_size = window_size
        self.buy_percentage = buy_percentage

    def __repr__(self):
        return "<Backtest " + str(self) + ">"
    
    
    def broker_action(self, qty: float, price: float, instruction: BrokerInstruction, num_stocks:float):
        arrStr = [["Energy_index", "loaned_Energy_index"],["Real_Estate_index","loaned_Real_Estate_index"],["Consumer_Cyclical_index","loaned_Consumer_Cyclical_index"]]
        arrVal = [[self.wallet['Energy_index'], self.wallet['loaned_Energy_index']],[self.wallet['Real_Estate_index'], self.wallet['loaned_Real_Estate_index']],[self.wallet['Consumer_Cyclical_index'], self.wallet['loaned_Consumer_Cyclical_index']]]
        i = instruction.sector.value -1
        nis_balance = (self.wallet["NIS"] - qty * num_stocks * price * self.commission)  # nis after commission
        loaned_NIS = self.wallet["loaned_NIS"]

        if instruction.order_type == OrderType.OPEN_LONG:
            self.wallet["NIS"] = nis_balance - (qty / self.leverage) * price
            self.wallet[arrStr[i][0]] = arrVal[i][0] + qty
            self.wallet["loaned_NIS"] = (
                loaned_NIS + (qty - (qty / self.leverage)) * price
            )
            return Position(qty, price, PositionSide.LONG, instruction.sector)
        
        elif instruction.order_type == OrderType.OPEN_SHORT:
            self.wallet["NIS"] = nis_balance + qty * price
            self.wallet[arrStr[i][0]] = arrVal[i][0] - (qty / self.leverage)
            self.wallet[arrStr[i][1]] = arrVal[i][1] + qty - (qty / self.leverage)
            return Position(qty, price, PositionSide.SHORT, instruction.sector)

        elif instruction.order_type == OrderType.CLOSE_LONG:
            self.wallet["NIS"] = nis_balance + qty * price - loaned_NIS
            self.wallet[arrStr[i][0]] = arrVal[i][0] - qty
            self.wallet["loaned_NIS"] = 0
            return None

        else:
            self.wallet["NIS"] = nis_balance - qty * price
            self.wallet[arrStr[i][0]] = arrVal[i][0] + (qty / self.leverage)
            self.wallet[arrStr[i][1]] = 0
            return None
    
    def update_balance(self, data:pd.DataFrame):
        self.balance = calculate_balance_type(data, "Open")
        balance_high = calculate_balance_type(data, "High")
        balance_low = calculate_balance_type(data, "Low")
        if balance_low <= 0 or balance_high <= 0:
            raise OutOfMoneyException
        return min(balance_low, balance_high)

    def calc_price(
        self, instructions: BrokerInstruction, sector_data: pd.DataFrame, change_size: int = 2.0
        ):
        curr_close = sector_data["Close"].sum()
        curr_open = sector_data["Open"].sum()

        slippage_rate = ((curr_close - curr_open) / curr_open) / change_size

        price = instructions.price

        if instructions.order_type in [OrderType.OPEN_LONG, OrderType.CLOSE_SHORT]:
            return max(price + price * slippage_rate, price)

        else:
            return min(price - price * slippage_rate, price)
    
    def calc_return(self, position: Position, close_price: float):
        open_price = position.price

        if position.side == PositionSide.SHORT:
            return_rate = (open_price - close_price) / open_price
        else:
            return_rate = (close_price - open_price) / open_price

        return return_rate * self.leverage
    
    def calc_return_with_comm(self, position: Position, close_price: float):
        open_price = position.price
        commission = position.price * self.commission + close_price * self.commission

        if position.side == PositionSide.SHORT:
            return_rate = (open_price - close_price - commission) / open_price
        else:
            return_rate = (close_price - open_price - commission) / open_price

        return return_rate * self.leverage


    def backtest(self):
            
            sectors = [Sector.ENERGY, Sector.REAL_ESTATE, Sector.CONSUMER_CYCLICAL]
            records_data = pd.DataFrame({
                                            "Date":[],
                                            "Balance":[],
                                            "Minimal balance":[],
                                            "NIS":[],
                                            "loaned NIS":[],
                                            "Open Energy":[],
                                            "Energy_index":[],
                                            "loaned_Energy_index":[],
                                            "Open Real Estate":[],
                                            "Real_Estate_index":[],
                                            "loaned_Real_Estate_index":[],
                                            "Open Consumer Cyclical":[],
                                            "Consumer_Cyclical_index":[],
                                            "loaned_Consumer_Cyclical_index":[],
                                            "Open Indices" :[],
                                            "Pos All":[],
                                            "Pos Energy":[],
                                            "Actions Energy":[],
                                            "Return rate Energy":[],
                                            "Return rate with comm Energy":[],
                                            "Pos Real Estate":[],
                                            "Actions Real Estate":[],
                                            "Return rate Real Estate":[],
                                            "Return rate with comm Real Estate":[],
                                            "Pos Consumer Cyclical":[],
                                            "Actions Consumer Cyclical":[],
                                            "Return rate Consumer Cyclical":[],
                                            "Return rate with comm Consumer Cyclical":[]
                                         })
            positions: np.array(Position) = [None,None,None]
            stocks_data = self.stocks_data.copy(deep=True).fillna(0)
            weather_data = self.weather_data.copy(deep=True).fillna(0)
            stocks_data['Date'] = pd.to_datetime(stocks_data['Date'])
            weather_data['Date'] = pd.to_datetime(weather_data['Date'])
            stocks_data['t0'] = (stocks_data['Date'] - self.start_day).dt.days.astype(int)
            weather_data['t0'] = (weather_data['Date'] - self.start_day).dt.days.astype(int)
            stocks_data['day_of_week'] = stocks_data['Date'].dt.dayofweek
            stocks_data = stocks_data[(stocks_data['day_of_week'] != 4) & (stocks_data['day_of_week'] != 5)]
            weather_data = grade_all_days(weather_data).reset_index()
            weather_data.columns = ['Date','t0','grade']
            no_tarde_days = stocks_data.groupby('Date').apply(is_trading_day).reset_index()
            no_tarde_days.columns = ['Date','is_trading']
            no_trading = no_tarde_days[no_tarde_days['is_trading'] == False]
            no_trading = no_trading['Date'].tolist()
            stocks_data = stocks_data[~stocks_data['Date'].isin(no_trading)]
                        
            l = np.intersect1d(np.unique(stocks_data['t0'].to_numpy()), weather_data['t0'].to_numpy()) 

            for i in l:
                
                #  data of the i'th day
                curr_stocks_data = stocks_data[stocks_data['t0'] == i].copy().reset_index()
                curr_weather_data = weather_data[(weather_data['t0'] >= i-self.window_size) & (weather_data['t0'] <= i+1)].copy().reset_index()
                grade = generate_relative_grade(curr_weather_data)
                #if filter_by_sector(curr_stocks_data, Sector.ENERGY)['Open'].sum() == 0:
                #    continue    
                
                # checks what the minimal balance is now 
                
                minimal_balance = update_balance(self, curr_stocks_data)
                records_data.loc[i, "Date"] = curr_weather_data.loc[0,'Date']
                records_data.loc[i, "Balance"] = self.balance
                records_data.loc[i, "Minimal balance"] = minimal_balance
                records_data.loc[i, "NIS"] = self.wallet["NIS"]
                records_data.loc[i, "loaned NIS"] = self.wallet["loaned_NIS"]
                records_data.loc[i, "Energy_index"] = self.wallet["Energy_index"]
                records_data.loc[i, "loaned_Energy_index"] = self.wallet["loaned_Energy_index"]
                records_data.loc[i, "Real_Estate_index"] = self.wallet["Real_Estate_index"]
                records_data.loc[i, "loaned_Real_Estate_index"] = self.wallet["loaned_Real_Estate_index"]
                records_data.loc[i, "Consumer_Cyclical_index"] = self.wallet["Consumer_Cyclical_index"]
                records_data.loc[i, "loaned_Consumer_Cyclical_index"] = self.wallet["loaned_Consumer_Cyclical_index"]
                
                for j in range(0, 3):

                    sector = sectors[j]
                    curr_sector_stocks_data = filter_by_sector(curr_stocks_data, sector)
                    position = positions[j]

                    records_data.loc[i, "Open " + sector.__str__()] = curr_sector_stocks_data["Open"].sum()

                    if position is None:
                        records_data.loc[i, "Pos " + sector.__str__()] = curr_sector_stocks_data["Open"].sum()
                        if i == max(l):
                            continue
                        instruction: BrokerInstruction = self.strategy.strategies[j].enter_position(curr_sector_stocks_data,grade)

                        if instruction is not None:
                            actual_price = self.calc_price(instruction, curr_sector_stocks_data)
                            qty = math.floor((self.balance * self.buy_percentage / actual_price)) * self.leverage
                            if qty == 0:
                                positions[j] = None    
                            else:
                                records_data.loc[i, "Actions " + sector.__str__()] = instruction.order_type.name
                                positions[j] = self.broker_action(qty, actual_price, instruction, len(curr_sector_stocks_data))
                        
                    else:
                        
                        if position.side == PositionSide.SHORT:
                            records_data.loc[i, "Pos " + sector.__str__()] = (
                            curr_sector_stocks_data["Open"].sum() - POSITION_MARGIN
                            )
                        else:
                            records_data.loc[i, "Pos " + sector.__str__()] = (
                            curr_sector_stocks_data["Open"].sum() + POSITION_MARGIN
                            )
                        
                        if i == max(l):

                            last_close = curr_sector_stocks_data['Close'].sum()
                        
                            if position.side == PositionSide.LONG:
                                instruction = BrokerInstruction(
                                OrderType.CLOSE_LONG, last_close,
                                sector
                                )
                        
                            else:
                                instruction = BrokerInstruction(
                                OrderType.CLOSE_SHORT, last_close,
                                sector
                                )
                    
                        else:
                            instruction = self.strategy.strategies[j].exit_position(curr_sector_stocks_data,grade)


                        if instruction is not None:
                            records_data.loc[i, "Actions " + sector.__str__()] = 0  # position closed
                            actual_price = self.calc_price(instruction, curr_sector_stocks_data)
                            return_rate = self.calc_return(position, actual_price)
                            return_rate_comm = self.calc_return_with_comm(
                                position, actual_price
                            )

                            records_data.loc[i, "Return rate " + sector.__str__()] = return_rate
                            records_data.loc[i, "Return rate with comm "  + sector.__str__()] = return_rate_comm
                            positions[j] = self.broker_action(
                            position.qty, actual_price, instruction, len(curr_sector_stocks_data)
                            )
            
                records_data.loc[i, "Open Indices"] = records_data.loc[i, "Open Energy"] + records_data.loc[i, "Open Consumer Cyclical"] + records_data.loc[i, "Open Real Estate"]
                records_data.loc[i, "Pos All"] = records_data.loc[i, "Pos Energy"] + records_data.loc[i, "Pos Consumer Cyclical"] + records_data.loc[i, "Pos Real Estate"]

            records_data = records_data.set_index('Date')
            #records_data.to_csv(f"results\lets.csv")
            return records_data




                    