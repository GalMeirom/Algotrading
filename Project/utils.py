from datetime import datetime as datetime
import pandas as pd
import numpy as np
import itertools
from models import Sector, OutOfMoneyException

# Temperature Heat Index
def THI(temp:float, humidity:float):
  return 0.8*temp + 0.1*humidity*(temp-14.4) + 46.6

# Heat Index
def HI(T:float, RH:float):
  return -8.784695 + 1.61139411 * T + 2.338549 * RH - 0.14611605 * T * RH - 1.2308094 * 0.01 * T*T - 4.0488500 * 0.01 * RH*RH + 8.5282 * 0.0001 * T*T * RH - 1.99 * 0.000001 * T*T * RH*RH

# Comfort Index
def CI(T:float, RH:float):
  return (T+RH)/2

# Discomfort Index
def DI(T:float, RH:float):
    return T - (0.55 - 0.0055 * RH) * (T - 14.5)

# Robaa's Index
def RI(temp:float, wet:float, wind:float):
    return 1.53 * temp - 0.32 * wet - 1.38 * wind + 44.65


def grade_function(mean_temp:float, gale:float, wet_temp:float, dew_point:float, mean_humid:float, rainfall:float, wind:float):
    return RI(mean_temp, wet_temp, wind)

    

def grade_daily(day):
    max_temp = day.iloc[0].loc['temperature_max']
    min_temp = day.iloc[0].loc['temperature_min']
    gale = day.iloc[0].loc['gale']
    mean_temp = day.iloc[0].loc['temperature_mean']
    wet_temp = day.iloc[0].loc['wet_temperature_mean']
    dew_point = day.iloc[0].loc['dew_point_mean']
    humiduty_mean = day.iloc[0].loc['humidity_mean']
    rainfall = day.iloc[0].loc['rainfall']
    wind = day.iloc[0].loc['wind_speed_mean']
    
    return grade_function(mean_temp, gale, wet_temp, dew_point, humiduty_mean, rainfall, wind)

def grade_all_days(data):
    return data.groupby(['Date', 't0']).apply(grade_daily)
    

def adjust_types_stocks(data:pd.DataFrame):
    data = data.astype(
        {
            "Date": str,
            "Open": float,
            "High": float,
            "Low": float,
            "Close": float,
            "Volume": float,
            "stock": str,
            "sector": str,
        }
    )
    return data

def adjust_types_weather(data:pd.DataFrame):
    data = data.astype(
        {
            "Date": str,
            "temperature_max": float,
            "temperature_min": float,
            "temperature_mean": float,
            "gale": float,
            "wet_temperature_mean": float,
            "dew_point_mean": float,
            "humidity_mean": float,
            "humidity_max": float,
            "wind_speed_mean": float,
            "rainfall": float,
        }
    )
    return data


def filter_by_sector(data:pd.DataFrame, sector:Sector):
        return data[data['sector'] == sector.__str__()]

def calculate_balance_type(self, data:pd.DataFrame , s:str) :
            arrVal = [[self.wallet['Energy_index'], self.wallet['loaned_Energy_index']],
                      [self.wallet['Real_Estate_index'], self.wallet['loaned_Real_Estate_index']],
                      [self.wallet['Consumer_Cyclical_index'], self.wallet['loaned_Consumer_Cyclical_index']]]
            return np.sum([self.wallet["NIS"],
                    arrVal[0][0] * filter_by_sector(data, Sector.ENERGY)[s].sum(),
                    arrVal[1][0] * filter_by_sector(data, Sector.REAL_ESTATE)[s].sum(),
                    arrVal[2][0] * filter_by_sector(data, Sector.CONSUMER_CYCLICAL)[s].sum(),
                -1* self.wallet["loaned_NIS"],
                -1* arrVal[0][1] * filter_by_sector(data, Sector.ENERGY)[s].sum(),
                -1* arrVal[1][1] * filter_by_sector(data, Sector.REAL_ESTATE)[s].sum(),
                -1* arrVal[2][1] * filter_by_sector(data, Sector.CONSUMER_CYCLICAL)[s].sum()])

def update_balance(self, data:pd.DataFrame):
        self.balance = calculate_balance_type(self,data, "Open")
        balance_high = calculate_balance_type(self,data, "High")
        balance_low = calculate_balance_type(self, data, "Low")
        if balance_low <= 0 or balance_high <= 0:
            raise OutOfMoneyException
        return min(balance_low, balance_high)

def is_trading_day(day:pd.DataFrame):
    if day.shape[0] > 50:
        return True
    else:
         return False
    
def generate_relative_grade(data:pd.DataFrame):
    if data.shape[0] == 1:
         return data.iloc[-1].loc['grade']
    tom = data.iloc[-1].loc['grade']
    arr = np.average(data['grade'].to_numpy()[:-1])
    return round(tom/arr, 3)

def findsubsets(s, n):
    return list(itertools.combinations(s, n))