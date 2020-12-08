import os

os.system("pip install pandas_datareader")
os.system("pip install fpdf")
os.system("pip install opencv-python")
os.system("pip install yfinance")
os.system("pip install reportlab")


import pandas_datareader as pdr
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import cv2

import email, smtplib, ssl
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 

from fpdf import FPDF  
import unite_multiple_pictures_into_pdf

tickerlist = ['LULU', 'TSN',  'ENPH', 'AMD']



def two_week_window(tickerlist):
    for ticker in tickerlist:
        if ticker == "LULU":
            short_window = 2
            long_window = 8
        elif ticker == "ENPH":
            short_window = 20
            long_window = 4
        elif ticker == "LNG":
            short_window = 5
            long_window = 10
        elif ticker == "AMD":
            short_window = 2
            long_window = 5
        elif ticker == "TSN":
            short_window = 5
            long_window = 20
        elif ticker == "DLR":
            short_window = 7
            long_window = 17
    return short_window, long_window

def one_month_window(tickerlist):
    for ticker in tickerlist:
        if ticker == "LULU":
            short_window = 6
            long_window = 20
        elif ticker == "ENPH":
            short_window = 20
            long_window = 4
        elif ticker == "LNG":
            short_window = 5
            long_window = 10
        elif ticker == "AMD":
            short_window = 3
            long_window = 12
        elif ticker == "TSN":
            short_window = 5
            long_window = 20
        elif ticker == "DLR":
            short_window = 7
            long_window = 17
    return short_window, long_window

def three_month_window(tickerlist):
    for ticker in tickerlist:
        if ticker == "LULU":
            short_window = 6
            long_window = 20
        elif ticker == "ENPH":
            short_window = 20
            long_window = 4
        elif ticker == "LNG":
            short_window = 5
            long_window = 10
        elif ticker == "AMD":
            short_window = 3
            long_window = 12
        elif ticker == "TSN":
            short_window = 5
            long_window = 20
        elif ticker == "DLR":
            short_window = 7
            long_window = 17
    return short_window, long_window

def yearly_window(tickerlist):
    for ticker in tickerlist:
        if ticker == "LULU":
            short_window = 30
            long_window = 80
        elif ticker == "ENPH":
            short_window = 30
            long_window = 80
        elif ticker == "LNG":
            short_window = 30
            long_window = 80
        elif ticker == "CONE":
            short_window = 60
            long_window = 100
        elif ticker == "WELL":
            short_window = 7
            long_window = 20
        elif ticker == "DLR":
            short_window = 30
            long_window = 90
    return short_window, long_window

def three_year_window(tickerlist):
    for ticker in tickerlist:
        if ticker == "LULU":
            short_window = 20
            long_window = 40
        elif ticker == "ENPH":
            short_window = 20
            long_window = 80
        elif ticker == "LNG":
            short_window = 25
            long_window = 100
        elif ticker == "CONE":
            short_window = 20
            long_window = 90
        elif ticker == "WELL":
            short_window = 25
            long_window = 100
        elif ticker == "DLR":
            short_window = 25
            long_window = 100
    return short_window, long_window

def two_week_report(tickerlist):
    for ticker in tickerlist:
        year = int(datetime.datetime.today().strftime('%Y'))
        month = int(datetime.datetime.today().strftime('%m'))
        day = int(datetime.datetime.today().strftime('%d'))
        if month == 1 and day < 14:
            month_start = 12
            year_start = year-1
            day_start = 14+day
        elif day < 14:
            year_start=year
            month_start=month-1
            day_start= 30 - day
        else:
            year_start=year
            month_start=month
            day_start= day - 14
        DATA = pdr.get_data_yahoo(ticker, 
                                  start=datetime.datetime(year_start, month_start, day_start), 
                                  end=datetime.datetime(year, month, day))
        # Initialize the short and long windows
        short_window, long_window = two_week_window(tickerlist)
#        short_window = 7
#        long_window = 30
        # Initialize the `signals` DataFrame with the `signal` column
        signals = pd.DataFrame(index=DATA.index)
        signals['signal'] = 0.0
        # Create short simple moving average over the short window
        signals['short_mavg'] = DATA['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
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
        DATA['Close'].plot(ax=ax1, color='r', lw=2.)

        #ADDED bollinger bands (2std)
        signals_two = pd.DataFrame(index=DATA.index)
        signals_two['upper_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() + 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
        signals_two['lower_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() - 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
        ax = signals_two[['upper_BB', 'lower_BB']].plot(ax=ax1, lw=1, alpha=0.4, color="black")
        ax.fill_between(DATA.index, signals_two['upper_BB'], signals_two['lower_BB'], color='#ADCCFF', alpha=0.4)
   
        # Plot the short and long moving averages
        signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)
        
        # Plot the buy signals
        ax1.plot(signals.loc[signals.positions == 1.0].index, 
                 signals.short_mavg[signals.positions == 1.0],
                 '^', markersize=10, color='m')
        # Plot the sell signals
        ax1.plot(signals.loc[signals.positions == -1.0].index, 
                 signals.short_mavg[signals.positions == -1.0],
                 'v', markersize=10, color='k')
        # Show the plot
        plt.title(ticker + " 2 Week Moving Average Crossover")
        plt.show()
        filename = ticker + "_2week_report.png"
        fig.savefig(r"Results/%s" %(filename))

def monthly_report(tickerlist):
    for ticker in tickerlist:
        year = int(datetime.datetime.today().strftime('%Y'))
        month = int(datetime.datetime.today().strftime('%m'))
        day = int(datetime.datetime.today().strftime('%d'))
        if month == 1:
            month_start = 12
            year_start = year-1
            day_start = 1
        else:
            year_start=year
            month_start=month-1
            day_start=1
        DATA = pdr.get_data_yahoo(ticker, 
                                  start=datetime.datetime(year_start, month_start, day_start), 
                                  end=datetime.datetime(year, month, day))
        # Initialize the short and long windows
        short_window, long_window = one_month_window(tickerlist)
#        short_window = 7
#        long_window = 30
        # Initialize the `signals` DataFrame with the `signal` column
        signals = pd.DataFrame(index=DATA.index)
        signals['signal'] = 0.0
        # Create short simple moving average over the short window
        signals['short_mavg'] = DATA['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
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
        DATA['Close'].plot(ax=ax1, color='r', lw=2.)
        #ADDED bollinger bands (2std)
        signals_two = pd.DataFrame(index=DATA.index)
        signals_two['upper_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() + 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
        signals_two['lower_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() - 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
        ax = signals_two[['upper_BB', 'lower_BB']].plot(ax=ax1, lw=1, alpha=0.4, color="black")
        ax.fill_between(DATA.index, signals_two['upper_BB'], signals_two['lower_BB'], color='#ADCCFF', alpha=0.4)
   
        # Plot the short and long moving averages
        signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)
        
        # Plot the buy signals
        ax1.plot(signals.loc[signals.positions == 1.0].index, 
                 signals.short_mavg[signals.positions == 1.0],
                 '^', markersize=10, color='m')
        # Plot the sell signals
        ax1.plot(signals.loc[signals.positions == -1.0].index, 
                 signals.short_mavg[signals.positions == -1.0],
                 'v', markersize=10, color='k')
        # Show the plot
        plt.title(ticker + " 1 Month Moving Average Crossover")
        plt.show()
        filename = ticker + "_1month_report.png"
        fig.savefig(r"Results/%s" %(filename))


def quarterly_report(tickerlist):
    for ticker in tickerlist:
        year = int(datetime.datetime.today().strftime('%Y'))
        month = int(datetime.datetime.today().strftime('%m'))
        day = int(datetime.datetime.today().strftime('%d'))
        if month < 3:
            if month == 1:
                month_start = 11
                year_start = year-1
                day_start = 1
            else:
                month_start = 12
                year_start = year-1
                day_start = 1
        else:
            year_start=year
            month_start=month-3
            day_start=1
        DATA = pdr.get_data_yahoo(ticker, 
                                  start=datetime.datetime(year_start, month_start, day_start), 
                                  end=datetime.datetime(year, month, day))
        # Initialize the short and long windows
        short_window, long_window = three_month_window(tickerlist)
#        short_window = 7
#        long_window = 30
        # Initialize the `signals` DataFrame with the `signal` column
        signals = pd.DataFrame(index=DATA.index)
        signals['signal'] = 0.0
        # Create short simple moving average over the short window
        signals['short_mavg'] = DATA['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
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
        DATA['Close'].plot(ax=ax1, color='r', lw=2.)
        #ADDED bollinger bands (2std)
        signals_two = pd.DataFrame(index=DATA.index)
        signals_two['upper_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() + 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
        signals_two['lower_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() - 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
        ax = signals_two[['upper_BB', 'lower_BB']].plot(ax=ax1, lw=1, alpha=0.4, color="black")
        ax.fill_between(DATA.index, signals_two['upper_BB'], signals_two['lower_BB'], color='#ADCCFF', alpha=0.4)
   
        # Plot the short and long moving averages
        signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)
        
        # Plot the buy signals
        ax1.plot(signals.loc[signals.positions == 1.0].index, 
                 signals.short_mavg[signals.positions == 1.0],
                 '^', markersize=10, color='m')
        # Plot the sell signals
        ax1.plot(signals.loc[signals.positions == -1.0].index, 
                 signals.short_mavg[signals.positions == -1.0],
                 'v', markersize=10, color='k')
        # Show the plot
        plt.title(ticker + " 3 Month Moving Average Crossover")
        plt.show()
        filename = ticker + "_3month_report.png"
        fig.savefig(r"Results/%s" %(filename))

def yearly_report(tickerlist):
    for ticker in tickerlist:
        year = int(datetime.datetime.today().strftime('%Y'))
        month = int(datetime.datetime.today().strftime('%m'))
        day = int(datetime.datetime.today().strftime('%d'))
        year_start = year - 1
        DATA = pdr.get_data_yahoo(ticker, 
                                  start=datetime.datetime(year_start, month, day), 
                                  end=datetime.datetime(year, month, day))
        # Initialize the short and long windows
        short_window, long_window = yearly_window(tickerlist)
#        short_window = 7
#        long_window = 30
        # Initialize the `signals` DataFrame with the `signal` column
        signals = pd.DataFrame(index=DATA.index)
        signals['signal'] = 0.0
        # Create short simple moving average over the short window
        signals['short_mavg'] = DATA['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
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
        # Plot the closing price
        DATA['Close'].plot(ax=ax1, color='r', lw=2.)
        signals_two = pd.DataFrame(index=DATA.index)
        
        
        signals_two['upper_BB'] = DATA['Close'].rolling(window=30, min_periods=1, center=False).mean() + 2 * DATA['Close'].rolling(window=30, min_periods=1, center=False).std()
        signals_two['lower_BB'] = DATA['Close'].rolling(window=30, min_periods=1, center=False).mean() - 2 * DATA['Close'].rolling(window=30, min_periods=1, center=False).std()
        ax = signals_two[['upper_BB', 'lower_BB']].plot(ax=ax1, lw=1, alpha=0.4, color="black")
        ax.fill_between(DATA.index, signals_two['upper_BB'], signals_two['lower_BB'], color='#ADCCFF', alpha=0.4)
        
        # Plot the short and long moving averages
        signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)
        # Plot the buy signals
        ax1.plot(signals.loc[signals.positions == 1.0].index, 
                 signals.short_mavg[signals.positions == 1.0],
                 '^', markersize=10, color='m')
        # Plot the sell signals
        ax1.plot(signals.loc[signals.positions == -1.0].index, 
                 signals.short_mavg[signals.positions == -1.0],
                 'v', markersize=10, color='k')
        # Show the plot
        plt.title(ticker + " 1 Year Moving Average Crossover")
        plt.show()
        filename = ticker + "_1year_report.png"
        cwd = os.getcwd()
        print(os.listdir(cwd))
        fig.savefig(r"Results/%s" %(filename))
        

def three_year_report(tickerlist):
    for ticker in tickerlist:
        year = int(datetime.datetime.today().strftime('%Y'))
        month = int(datetime.datetime.today().strftime('%m'))
        day = int(datetime.datetime.today().strftime('%d'))
        year_start = year - 3
        DATA = pdr.get_data_yahoo(ticker, 
                                  start=datetime.datetime(year_start, month, day), 
                                  end=datetime.datetime(year, month, day))
        # Initialize the short and long windows
        short_window, long_window = three_year_window(tickerlist)
#        short_window = 7
#        long_window = 30
        # Initialize the `signals` DataFrame with the `signal` column
        signals = pd.DataFrame(index=DATA.index)
        signals['signal'] = 0.0
        # Create short simple moving average over the short window
        signals['short_mavg'] = DATA['Close'].rolling(window=short_window, min_periods=1, center=False).mean()
        # Create long simple moving average over the long window
        signals['long_mavg'] = DATA['Close'].rolling(window=long_window, min_periods=1, center=False).mean()
        # Create signals
        signals['signal'][short_window:] = np.where(signals['short_mavg'][short_window:] > signals['long_mavg'][short_window:], 1.0, 0.0)   
        # Generate trading orders
        signals['positions'] = signals['signal'].diff()
        # Print `signals`
        #print(signals)
        # Initialize the plot figure
        fig = plt.figure(figsize=(6, 4))
        # Add a subplot and label for y-axis
        ax1 = fig.add_subplot(111,  ylabel='Price in $')
        # Plot the closing price
        DATA['Close'].plot(ax=ax1, color='r', lw=2.)
        
        signals_two = pd.DataFrame(index=DATA.index)
        signals_two['upper_BB'] = DATA['Close'].rolling(window=80, min_periods=1, center=False).mean() + 2 * DATA['Close'].rolling(window=80, min_periods=1, center=False).std()
        signals_two['lower_BB'] = DATA['Close'].rolling(window=80, min_periods=1, center=False).mean() - 2 * DATA['Close'].rolling(window=80, min_periods=1, center=False).std()
        ax = signals_two[['upper_BB', 'lower_BB']].plot(ax=ax1, lw=1, alpha=0.4, color="black")
        ax.fill_between(DATA.index, signals_two['upper_BB'], signals_two['lower_BB'], color='#ADCCFF', alpha=0.4)
        
        # Plot the short and long moving averages
        signals[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)
        # Plot the buy signals
        ax1.plot(signals.loc[signals.positions == 1.0].index, 
                 signals.short_mavg[signals.positions == 1.0],
                 '^', markersize=10, color='m')
        # Plot the sell signals
        ax1.plot(signals.loc[signals.positions == -1.0].index, 
                 signals.short_mavg[signals.positions == -1.0],
                 'v', markersize=10, color='k')
        # Show the plot
        plt.title(ticker + " 3 Year Moving Average Crossover")
        plt.show()
        filename = ticker + "_3year_report.png"
        fig.savefig(r"Results/%s" %(filename))
        
        
        

def create_report(tickerlist,user_email):
    
    os.system("python3 unite_multiple_pictures_into_pdf.py")
    
    subject = "An email with attachment from Python"
    body = "This is an email with attachment sent from Python"
    sender_email = "stockanalysis553@gmail.com"
    receiver_email = user_email
    password = "stocksarecool9853!"
     # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject
    # message["Bcc"] = receiver_email  # Recommended for mass emails
    
    # Add body to email
    message.attach(MIMEText(body, "plain"))
    
    filename = "FinalResults_ALL_1-20_of_20.pdf"  # In same directory as script
    
    # Open PDF file in binary mode
    filepath = os.getcwd() + '/Results/' + filename
    with open(filepath, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    
    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)
    
    # Add header as key/value pair to attachment part
    part.add_header("Content-Disposition",f"attachment; filename= {filename}",)
    
     # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()
    
     # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login("stockanalysis553", password)
        server.sendmail(sender_email, receiver_email, text)
    
    
def main(tickerlist):
    quarterly_report(tickerlist)
    yearly_report(tickerlist)
    three_year_report(tickerlist)
    monthly_report(tickerlist)
    two_week_report(tickerlist)
    user_email = input("Enter email for the analytics report: ")
    create_report(tickerlist,user_email)

if __name__ == "__main__":
    main(tickerlist)