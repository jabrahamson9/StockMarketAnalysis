import pandas_datareader as pdr
import datetime
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

tickerlist = ['LULU', 'TSN']

def RSI(ticker, daysBack, DATA):
    # DATA = pdr.get_data_yahoo(ticker,
    #                         start = datetime.datetime.today() - timedelta(days=daysBack+14),
    #                         end = datetime.datetime.today())
    DATA.index = pd.to_datetime(DATA.index).strftime('%Y-%m-%d')
    avgUp = []
    avgDown = []
    for i in range(daysBack):
        up = []
        down = []
        prevClose = DATA.at[DATA.index[i], 'Close']
        base = datetime.datetime.strptime(DATA.index[i], '%Y-%m-%d')
        date_list = [base + timedelta(days=x) for x in range(14)]
        # print(date_list)
        for index, row in DATA.iterrows():
            index = datetime.datetime.strptime(index, '%Y-%m-%d')
            if index in date_list:
                if row['Close'] > prevClose:
                    up.append(row['Close']-prevClose)
                elif row['Close'] < prevClose:
                    down.append(prevClose - row['Close'])
                prevClose = row['Close']
        if len(up) == 0:
            avgUp.append(0)
        else:
            avgUp.append(sum(up)/len(up))
        if len(down) == 0:   
            avgDown.append(0)
        else:
            avgDown.append(sum(down)/len(down))
    RSI = []
    for x in range(len(avgUp)):
        RSvalue = (avgUp[x] / avgDown[x])
        RSI.append(100 - (100 / (1+RSvalue)))
    return RSI


def StoOsc(ticker, daysBack, DATA):
    # DATA = pdr.get_data_yahoo(ticker,
    #                         start = datetime.datetime.today() - timedelta(days=daysBack),
    #                         end = datetime.datetime.today())
    DATA['L14'] = DATA['Low'].rolling(window=14).min()
    #Create the "H14" column in the DataFrame
    DATA['H14'] = DATA['High'].rolling(window=14).max()
    #Create the "%K" column in the DataFrame
    DATA['%K'] = 100*((DATA['Close'] - DATA['L14']) / (DATA['H14'] - DATA['L14']) )
    #Create the "%D" column in the DataFrame
    DATA['%D'] = DATA['%K'].rolling(window=3).mean()
    fig, axes = plt.subplots(nrows=2, ncols=1,figsize=(15,7))
    DATA['Close'].plot(ax=axes[0]); axes[0].set_title('Close')
    DATA[['%K','%D']].plot(ax=axes[1]); axes[1].set_title('Oscillator')
    #plt.show()
    return list(DATA['%K']), list(DATA['%D'])

def MA(ticker, daysBack, DATA):
    # DATA = pdr.get_data_yahoo(ticker,
    #                         start = datetime.datetime.today() - timedelta(days=daysBack),
    #                         end = datetime.datetime.today())
    short_window = 5
    long_window = 30
    # Initialize the `signals` DataFrame with the `signal` column
    signals = pd.DataFrame(index=DATA.index)
    signals['signal'] = 0.0
    # Create short simple moving average over the short window
    #signals['short_mavg'] = DATA['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
    signals['short_mavg'] = DATA['Close'].ewm(span=short_window).mean()
    # Create long simple moving average over the long window
    signals['long_mavg'] = DATA['Close'].rolling(window=long_window, min_periods=1, center=False).mean()
    # Create signals
    signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)   
    # Generate trading orders
    signals['positions'] = signals['signal'].diff()
    # Initialize the plot figure
    fig = plt.figure(figsize=(6, 4))
    # Add a subplot and label for y-axis
    ax1 = fig.add_subplot(111,  ylabel='Price in $')
    DATA['Close'].plot(ax=ax1, color='r', lw=2.0)
    signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.0)
    # Plot the buy signals
    ax1.plot(signals.loc[signals.positions == 1.0].index, 
                signals.short_mavg[signals.positions == 1.0],
                '^', markersize=10, color='m')
    # Plot the sell signals
    ax1.plot(signals.loc[signals.positions == -1.0].index, 
                signals.short_mavg[signals.positions == -1.0],
                'v', markersize=10, color='k')
    #plt.show()
    return list(signals['positions']), list(signals['short_mavg']), list(signals['long_mavg'])

def Boll(ticker, daysBack, DATA):
    # DATA = pdr.get_data_yahoo(ticker,
    #                         start = datetime.datetime.today() - timedelta(days=daysBack),
    #                         end = datetime.datetime.today())
    fig = plt.figure(figsize=(6, 4))
    ax1 = fig.add_subplot(111,  ylabel='Price in $')
    signals_two = pd.DataFrame(index=DATA.index)
    signals_two['upper_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() + 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
    signals_two['lower_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() - 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
    ax = signals_two[['upper_BB', 'lower_BB']].plot(ax=ax1, lw=1, alpha=0.4, color="black")
    ax.fill_between(DATA.index, signals_two['upper_BB'], signals_two['lower_BB'], color='#ADCCFF', alpha='0.4')
    DATA['Close'].plot(ax=ax1, color='r', lw=2.0)
    plt.show()
    return list(signals_two['upper_BB']), list(signals_two['lower_BB']), list(DATA['Close'])

def stockVal(ticker, daysBack):
    DATA = pdr.get_data_yahoo(ticker,
                            start = datetime.datetime.today() - timedelta(days=daysBack),
                            end = datetime.datetime.today())   
    DATA_RSI = pdr.get_data_yahoo(ticker,
                            start = datetime.datetime.today() - timedelta(days=daysBack+14),
                            end = datetime.datetime.today())   

    Boll_Val = 0
    Sto_Val = 0
    MA_Val = 0
    RSI_Val = 0

    RSI = RSI(tickerlist, daysBack, DATA_RSI)
    K,D = StoOsc(tickerlist, daysBack, DATA)
    sig, shortMA, longMA = MA(tickerlist, daysBack, DATA)
    up, low, close = Boll(tickerlist, daysBack, DATA)

    prev_short = shortMA[0]
    prev_long = longMA[0]
    prev_K = K[0]
    prev_D = D[0]
    for i in range(close):
        if close[i] > up[i]:
            Boll_Val = -1
        elif close[i] < low[i]:
            Boll_Val = 1

        if shortMA[i] > longMA[i] and prev_short < prev_long:
            MA_Val = 1
        elif shortMA[i] < longMA[i] and prev_short > prev_long:
            MA_Val = -1
        prev_short = shortMA[i]
        prev_long = longMA[i]

        if K[i] < D[i] and prev_K > prev_D and K[i] >= 80:
            Sto_Val = -1
        elif K[i] > D[i] and prev_K < prev_D and K[i] <= 20:
            Sto_Val = 1

stockVal('LULU', 365)