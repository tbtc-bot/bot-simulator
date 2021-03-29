import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import util


def plotCandlesticks():
    df = pd.read_csv('datasets/LTC.csv', parse_dates=['Date'])

    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df['Date'],
                                 open=df['Open'],
                                 high=df['High'],
                                 low=df['Low'],
                                 close=df['Close'],
                                 name='LTC'))
    fig.update_layout(
        title="LTC/USDT",
        xaxis_title="Time",
        yaxis_title="Price"
    )
    fig.show()


def plotMetrics(df, strategyName, savePath=None):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 8), sharex='col')

    figName = strategyName.replace('_', ', ')
    fig.suptitle(figName, fontsize=14)

    x = df.index

    ax1.plot(x, df['MarkPrice'], linewidth=1.3)
    ax1.set_ylabel('Price $')
    ax1.grid()

    ax2.plot(x, df['Equity'], linewidth=1)
    ax2.fill_between(x, df['Equity'][0], df['Equity'], alpha=0.5)
    ax2.set_ylabel('Equity $')
    ax2.ticklabel_format(axis='y', useOffset=False)
    ax2.grid()

    ax3.plot(x, df['Drawdown %'], color='red', linewidth=1)
    ax3.fill_between(x, 0, df['Drawdown %'], alpha=0.5, facecolor='red')
    ax3.set_ylabel('Drawdown %')
    ax3.set_xlabel('Time')
    ax3.grid()

    if savePath is not None:
        fig.savefig(savePath)


def plotDistributions(df):
    # get grid reached for each profit
    profitGridReached = []
    for i in range(len(df.index)):
        if not np.isnan(df['NetProfit'][i]):
            profitGridReached.append(df['GridReached'][i])

    data = np.array(profitGridReached)
    bins = np.arange(0, data.max() + 1.5) - 0.5
    fig, ax = plt.subplots()
    ax.hist(data, bins, rwidth=0.7, density=True)
    ax.set_xticks(bins + 0.5)
    ax.set_xlim([0.1, data.max() + 0.9])
    ax.set_title('Distribution of TP grids')
    ax.set_ylabel('Frequency')
    ax.set_xlabel('Grid Number')

    # compute profit contribution of each grid
    gridProfitDict = {}
    for i in range(len(df.index)):
        netProfit = df['NetProfit'][i]

        if not np.isnan(netProfit):
            grid = int(df['GridReached'][i])
            if grid in gridProfitDict:
                gridProfitDict[grid] += netProfit
            else:
                gridProfitDict[grid] = netProfit

    # check the sum of grid profits is equal to the total profit
    totalNetProfit = df['NetProfit'].sum()
    if abs(totalNetProfit - sum(list(gridProfitDict.values()))) > 0.0001:
        util.logger.error("The sum of the grid profits is not equal to the total profits")

    nGrids = int(max(list(gridProfitDict.keys())))
    data = []
    for i in range (nGrids):
        if (i+1) in gridProfitDict:
            data.append(gridProfitDict[i+1] / totalNetProfit * 100)
        else:
            gridProfitDict[i] = 0
            data.append(0)

    fig, ax = plt.subplots()
    ax.bar(range(1,nGrids+1), data)
    ax.set_xticks(bins + 0.5)
    ax.set_xlim([0.1, nGrids + 0.9])
    ax.set_title('Distribution of profits by grid')
    ax.set_ylabel('Profit %')
    ax.set_xlabel('Grid Number')


def toRename(df, caseStudy, filePath):
    profit = df['Equity'].iloc[-1] - df['Equity'][0]
    maxDrawdown = df['Drawdown %'].min()
    with open(filePath,'a') as f:
        f.write(f'{caseStudy} -> profit: {profit}, maxDrawdown: {maxDrawdown}\n')
