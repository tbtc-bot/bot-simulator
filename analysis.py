import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import util


font = {#'family': 'serif',
        # 'color':  'darkred',
        'weight': 'normal',
        'size': 12,
        }


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
    p0 = df['MarkPrice'][0]
    e0 = df['Equity'][0]

    ax1.set_title('Price')
    ax1.plot(x, df['MarkPrice'], linewidth=1.3)
    lbl = ax1.set_ylabel('$', labelpad=10)
    lbl.set_rotation(0)
    ax1b = ax1.twinx()
    ax1b.plot(x, (df['MarkPrice'] - p0) / p0 * 100, linewidth=0)
    lbl = ax1b.set_ylabel('%', labelpad=10)
    lbl.set_rotation(0)
    ax1.grid()

    ax2.set_title('Equity')
    ax2.plot(x, df['Equity'], linewidth=1)
    ax2.fill_between(x, df['Equity'][0], df['Equity'], alpha=0.5)
    lbl = ax2.set_ylabel('$', labelpad=10)
    lbl.set_rotation(0)
    ax2.ticklabel_format(axis='y', useOffset=False)
    ax2b = ax2.twinx()
    ax2b.plot(x, (df['Equity'] - e0) / e0 * 100, linewidth=0)
    lbl = ax2b.set_ylabel('%', labelpad=10)
    lbl.set_rotation(0)
    ax2.grid()

    ax3.set_title('Drawdown')
    ax3.plot(x, df['Drawdown %'] * e0/100, color='red', linewidth=1)
    lbl = ax3.set_ylabel('$', labelpad=10)
    lbl.set_rotation(0)
    ax3.set_xlabel('Time', labelpad=10)
    ax3b = ax3.twinx()
    ax3b.plot(x, df['Drawdown %'], color='red', linewidth=0)
    ax3b.fill_between(x, 0, df['Drawdown %'], alpha=0.5, facecolor='red')
    lbl = ax3b.set_ylabel('%', labelpad=10)
    lbl.set_rotation(0)
    ax3.grid()
    fig.tight_layout()
    if savePath is not None:
        fig.savefig(savePath)


def plotDistributions(df, savePath=None):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    # fig.suptitle('Distribution of take profits', fontsize=14)

    # get grid reached for each profit
    profitGridReached = []
    for i in range(len(df.index)):
        if not np.isnan(df['NetProfit'][i]):
            profitGridReached.append(df['GridReached'][i])

    data = np.array(profitGridReached)
    bins = np.arange(0, data.max() + 1.5) - 0.5
    ax1.hist(data, bins, rwidth=0.7, density=True)
    ax1.set_xticks(bins + 0.5)
    ax1.set_xlim([0.1, data.max() + 0.9])
    ax1.set_title('Distribution of TP grids', fontdict=font)
    ax1.set_ylabel('Frequency', fontdict=font)
    ax1.set_xlabel('Grid Number', fontdict=font)

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

    # distribution of profits
    ax2.bar(range(1,nGrids+1), data)
    ax2.set_xticks(bins + 0.5)
    ax2.set_xlim([0.1, nGrids + 0.9])
    ax2.set_title('Distribution of by grid', fontdict=font)
    ax2.set_ylabel('Profit %', fontdict=font)
    ax2.set_xlabel('Grid Number', fontdict=font)

    fig.tight_layout()
    fig.subplots_adjust(wspace=0.15)
    if savePath is not None:
        fig.savefig(savePath)


def toRename(df, caseStudy, filePath):
    profit = df['Equity'].iloc[-1] - df['Equity'][0]
    maxDrawdown = df['Drawdown %'].min()
    with open(filePath,'a') as f:
        f.write(f'{caseStudy} -> profit: {profit}, maxDrawdown: {maxDrawdown}\n')
