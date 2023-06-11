import pandas as pd
import numpy as np
import datetime
import psutil
from backtest_weather import Backtest_weather
from backtest import Backtest
from strategies import RandomStrategy, Weather_BH
from summary import Summary, plot_data

from utils import adjust_types_stocks, adjust_types_weather, findsubsets 
import itertools
 

 
# main for BH
# def main():
#     dates = pd.read_csv('data\dates.csv')
#     strats = np.array(list(map(lambda x : datetime.datetime.strptime(x[:-1], '%Y-%m-%d'), np.unique(dates['s'].to_numpy()))))
#     ends = np.array(list(map(lambda x : datetime.datetime.strptime(x[:-1], '%Y-%m-%d'), np.unique(dates['e'].to_numpy()))))
#     i = 0
#     start_date = strats[i]
#     end_date = ends[i]
#     stocks_data = pd.read_csv("data\stocks_data\stocks_data.csv")
#     weather_data = pd.read_csv("data\weather_data\weather_data.csv")
#     stocks_data = adjust_types_stocks(stocks_data)
#     weather_data = adjust_types_weather(weather_data)
#     stocks_data['Date'] = pd.to_datetime(stocks_data['Date'], format= "%d/%m/%Y")
#     weather_data['Date'] = pd.to_datetime(weather_data['Date'], format= "%d/%m/%Y")
#     df = pd.DataFrame({
#         'max_balance_drowdown':[],
#         'max_drawdown':[],
#         'returns_std':[],
#         'total_return':[],
#         'sharpe' :[],
#         'downside_deviation':[],
#         'sortino':[],
#         'calmar_ratio':[],
#         "trades":[],
#         "positive_trades":[],
#         "positive_trading_days":[] 
#     })
#     back = Backtest(
#         strat_day=start_date,
#         end_day=end_date,
#         stocks_data= stocks_data,
#         weather_data= weather_data,
#         stratagy= Weather_BH(),
#         commission=0.0002, balance=10000000
#     )
#     trading_data = back.backtest()
#     summary = Summary(trading_data)
#     #summary.print_results()
#     summary.output(df, 0)
#     df.to_csv(f"results\opt.csv")



# main for the actual strategy


def main():
    dates = pd.read_csv('data\dates.csv')
    strats = np.array(list(map(lambda x : datetime.datetime.strptime(x[:-1], '%Y-%m-%d'), np.unique(dates['s'].to_numpy()))))
    ends = np.array(list(map(lambda x : datetime.datetime.strptime(x[:-1], '%Y-%m-%d'), np.unique(dates['e'].to_numpy()))))
    i = 1
    start_date = strats[i]
    end_date = ends[i]
    stocks_data = pd.read_csv("data\stocks_data\stocks_data.csv")
    weather_data = pd.read_csv("data\weather_data\weather_data.csv")
    stocks_data = adjust_types_stocks(stocks_data)
    weather_data = adjust_types_weather(weather_data)
    stocks_data['Date'] = pd.to_datetime(stocks_data['Date'], format= "%d/%m/%Y")
    weather_data['Date'] = pd.to_datetime(weather_data['Date'], format= "%d/%m/%Y")
    #s = set([0.6, 0.68, 0.76, 0.84, 0.92, 1, 1.08, 1.16, 1.24, 1.32, 1.4])
    s = set([0.85, 0.91, 0.97, 1.03, 1.09, 1.15])
    lst = findsubsets(s, 4)
    df = pd.DataFrame({
        'max_balance_drowdown':[],
        'max_drawdown':[],
        'returns_std':[],
        'total_return':[],
        'sharpe' :[],
        'downside_deviation':[],
        'sortino':[],
        'calmar_ratio':[],
        "en_inU":[],
        "en_outU":[],
        "en_outD":[], 
        "en_inD":[],
        "re_inU":[], 
        "re_outU":[], 
        "re_outD":[], 
        "re_inD":[],
        "cc_inU":[], 
        "cc_outU":[], 
        "cc_outD":[],
        "cc_inD":[],
        "trades":[],
        "positive_trades":[],
        "positive_trading_days":[] 
    })
    j=0
    for a in lst:
        for b in lst:
            for c in lst:
                en = list(sorted(a))
                re = list(sorted(b))
                cc = list(sorted(c))
                print('The CPU usage is: ', psutil.cpu_percent(4))
                print('RAM memory % used:', psutil.virtual_memory()[2])
                back = Backtest_weather(start_date,end_date,stocks_data,weather_data, commission=0.0002, balance=10000000,
                                        en_inU= en[3] , en_outU= en[2], en_outD= en[1], en_inD= en[0],
                                        re_inU= re[3], re_outU= re[2], re_outD= re[1], re_inD= re[0],
                                        cc_inU= cc[3], cc_outU= cc[2], cc_outD= cc[1], cc_inD= cc[0])
                trading_data = back.backtest()
                summary = Summary(trading_data)
                #summary.print_results()
                summary.output(df, j)
                df.loc[j,"en_inU"] = en[3]
                df.loc[j,"en_outU"] = en[2]
                df.loc[j,"en_outD"] = en[1]
                df.loc[j,"en_inD"] = en[0]
                df.loc[j,"re_inU"] = re[3]
                df.loc[j,"re_outU"] = re[2]
                df.loc[j,"re_outD"] = re[1]
                df.loc[j,"re_inD"] = re[0]
                df.loc[j,"cc_inU"] = cc[3]
                df.loc[j,"cc_outU"] = cc[2]
                df.loc[j,"cc_outD"] = cc[1]
                df.loc[j,"cc_inD"] = cc[0]
                j = j +1
    df.to_csv(f"results\opt_1.csv")
    #plot_data(trading_data)



if __name__ == "__main__":
    main()
