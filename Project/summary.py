from math import sqrt
import pandas as pd
import numpy as np
import plotly.express as px

import seaborn as sns

from matplotlib import pyplot as plt
from simple_colors import red


class Summary:
    def __init__(self, data=None):
        self.max_balance_drowdown = None
        self.max_drawdown = None
        self.returns_std = None
        self.total_return = None
        self.sharpe = None
        self.downside_deviation = None
        self.sortino = None
        self.best_trade = None
        self.worst_trade = None
        self.calmar_ratio = None
        self.positive_trades = None
        self.positive_trading_days = None
        self.trades = None
        if type(data) != str:
            self.init(data)
        else:
            self.init_from_csv(data)

    def print_results(self):
        print(red("Total return:", "bold"), f"{self.total_return}%")
        print(red("Sharpe:", "bold"), f"{self.sharpe}%")
        print(red("Sortino:", "bold"), f"{self.sortino}%")
        print(red("Max balance drawdown:", "bold"), f"{self.max_balance_drowdown}%")
        print(red("Max drawdown:", "bold"), f"{self.max_drawdown}%")
        print(red("Returns std:", "bold"), f"{self.returns_std}%")
        print(red("Downside deviation:", "bold"), f"{self.downside_deviation}%")
        print(red("Best trade:", "bold"), f"{self.best_trade}%")
        print(red("Worst trade:", "bold"), f"{self.worst_trade}%")
        print(red("Positive trades:", "bold"), f"{self.positive_trades}%")
        print(red("Positive trading days:", "bold"), f"{self.positive_trading_days}%")

    #def init_from_csv(self, csv_path):
    #    data = pd.read_csv(csv_path)
    #    data = adjust_types(data)
    #    self.init(data)

    def output(self, data:pd.DataFrame, i:int):
        data.loc[i,'max_balance_drowdown'] = self.max_balance_drowdown
        data.loc[i,'max_drawdown'] = self.max_drawdown
        data.loc[i,'returns_std'] = self.returns_std
        data.loc[i,'total_return'] = self.total_return
        data.loc[i,'sharpe'] = self.sharpe 
        data.loc[i,'downside_deviation'] = self.downside_deviation
        data.loc[i,'sortino'] = self.sortino
        data.loc[i,'calmar_ratio'] = self.calmar_ratio
        data.loc[i,'trades'] = self.trades
        data.loc[i,'positive_trades'] = self.positive_trades
        data.loc[i,'positive_trading_days'] = self.positive_trading_days


    def init(self, data:pd.DataFrame):
        # max_balance_drowdown
        min_balance = min(data["Balance"])
        initial_balance = data["Balance"].iloc[0]
        self.max_balance_drowdown = round(
            (1 - (min_balance / initial_balance)) * 100, 3
        )
        temp = data['Return rate with comm Energy'].fillna(0).to_numpy() + data['Return rate with comm Real Estate'].fillna(0).to_numpy()+ data['Return rate with comm Consumer Cyclical'].fillna(0).to_numpy()
        data['Return rate with comm'] = temp.tolist()
        temp = data['Return rate Energy'].fillna(0).to_numpy() + data['Return rate Real Estate'].fillna(0).to_numpy()+ data['Return rate Consumer Cyclical'].fillna(0).to_numpy()
        data['Return rate'] = temp.tolist()
        # returns_std, convert to a series
        daily_returns_series = data[["Return rate with comm"]].iloc[:, 0]

        # max drawdown
        cumulative_max = daily_returns_series.cummax()
        drawdown = cumulative_max - daily_returns_series
        self.max_drawdown = round(drawdown.max() * 100, 3)

        # resample by day to get daily return
        returns_std = daily_returns_series.std() * 100
        self.returns_std = round(returns_std, 3)

        # total_return
        end_balance = data["Balance"].iloc[-1]
        total_return = ((end_balance - initial_balance) / initial_balance) * 100
        self.total_return = round(total_return, 3)

        # sharpe ratio = total return percentage / standard deviation * sqrt(num of trading days)
        self.sharpe = round(
            total_return / (returns_std * sqrt(len(daily_returns_series))), 3
        )

        # downside deviation
        # remove positive returns
        negative_returns_std = (
            daily_returns_series.apply(lambda x: x if x < 0 else np.nan).dropna()
        ).std() / sqrt(len(daily_returns_series))
        self.downside_deviation = round(negative_returns_std * 100, 3)

        # sortino - same as sharpe but using downside deviation instead of regular std
        self.sortino = round(total_return / negative_returns_std, 3)

        # best and worse trade
      #  a = max(data['Return rate with comm Energy'].to_numpy()[~np.isnan(data['Return rate with comm Energy'].to_numpy())])
      #  b = max(data['Return rate with comm Real Estate'].to_numpy()[~np.isnan(data['Return rate with comm Real Estate'].to_numpy())])
      #  c = max(data['Return rate with comm Consumer Cyclical'].to_numpy()[~np.isnan(data['Return rate with comm Consumer Cyclical'].to_numpy())])
      #  self.best_trade = round(max(a,b,c) * 100, 3)
      #  a = min(data['Return rate with comm Energy'].to_numpy()[~np.isnan(data['Return rate with comm Energy'].to_numpy())])
      #  b = min(data['Return rate with comm Real Estate'].to_numpy()[~np.isnan(data['Return rate with comm Real Estate'].to_numpy())])
      #  c = min(data['Return rate with comm Consumer Cyclical'].to_numpy()[~np.isnan(data['Return rate with comm Consumer Cyclical'].to_numpy())])
      #  self.worst_trade = round(min(a,b,c) * 100, 3)
    
        # Percentage of positive trades
        trades_E = data["Return rate with comm Energy"].dropna()
        trades_R = data["Return rate with comm Real Estate"].dropna()
        trades_C = data["Return rate with comm Consumer Cyclical"].dropna()
        trades = len(trades_E) + len(trades_R) + len(trades_C)
        self.trades = trades
        trades_E = trades_E.apply(lambda x: x if x > 0 else np.nan).dropna()
        trades_R = trades_R.apply(lambda x: x if x > 0 else np.nan).dropna()
        trades_C = trades_C.apply(lambda x: x if x > 0 else np.nan).dropna()
        profitable_trades = len(trades_E) + len(trades_R) + len(trades_C)
        if trades == 0:
            self.positive_trades = 0
        else:    
            self.positive_trades = round((profitable_trades / trades) * 100, 3)

        # profitable_days
        profitable_days = daily_returns_series.apply(
            lambda x: x if x > 0 else np.nan
        ).dropna()
        self.positive_trading_days = round(
            (len(profitable_days) / len(daily_returns_series)) * 100, 3
        )
    

def plot_data(df):
    fig = px.line(df, x=df.index, y="Open Energy", title="Protfolio over Energy index size over time")
    fig.add_scatter(x=df.index, y=df["Pos Energy"], mode="lines", name="Portfolio Position")
    fig.show()
    
    fig = px.line(df, x=df.index, y="Open Real Estate", title="Protfolio over Real Estate index size over time")
    fig.add_scatter(x=df.index, y=df["Pos Real Estate"], mode="lines", name="Portfolio Position")
    fig.show()

    fig = px.line(df, x=df.index, y="Open Consumer Cyclical", title="Protfolio over Consumer Cyclical index size over time")
    fig.add_scatter(x=df.index, y=df["Pos Consumer Cyclical"], mode="lines", name="Portfolio Position")
    fig.show()
        
    fig = px.line(df, x=df.index, y="Open Indices", title="Protfolio size over three indices over time")
    fig.add_scatter(x=df.index, y=df["Pos All"], mode="lines", name="Portfolio Position")
    fig.show()

    fig = px.line(
        df, x=df.index, y="Balance", title="Protfolio size over time", render_mode="SVG"
    )
    fig.show()

    fig = px.line(
        df, x=df.index, y="Minimal balance", title="Minimal balance over time"
    )
    fig.show()

    fig = px.box(df, y="Return rate")
    fig.show()

    #sns.distplot(df["Return rate"], rug=True, kde=True)
    #plt.show()


def main():
    path = "detailed_summaries/l&s-btc-fl25000000-sl50000000-rand3095.csv"
    df = pd.read_csv(path)
    summary = Summary(path)
    print(summary)
    plot_data(df)


if __name__ == "__main__":

    main()
