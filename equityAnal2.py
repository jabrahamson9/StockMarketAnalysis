import os
import sys

# os.system("python -m pip install pandas_datareader")
# os.system("python -m pip install fpdf")
# os.system("python -m pip install opencv-python")
# os.system("python -m pip install yfinance")
# os.system("python -m pip install reportlab")

import pandas_datareader as pdr
import datetime
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from operator import itemgetter
import tkinter as tk

import email, smtplib, ssl
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 

from fpdf import FPDF  

import glob
import re
from reportlab.lib import utils
from reportlab.pdfgen import canvas
from unite_multiple_pictures_into_pdf import sorted_nicely, unite_pictures_into_pdf

import csv

def RSI(ticker, DATA):
    DATA.index = pd.to_datetime(DATA.index).strftime('%Y-%m-%d')
    avgUp = []
    avgDown = []
    up = []
    down = []
    for i in range(14, -1, -1):
        prev = DATA.index[len(DATA) - i - 2]
        curr = DATA.index[len(DATA) - i - 1]
        prevClose = DATA.at[prev, 'Close']
        curClose = DATA.at[curr, 'Close']
        if curClose > prevClose:
            up.append(curClose - prevClose)
        elif curClose < prevClose:
            down.append(prevClose - curClose)
    if len(up) == 0:
        avgUp = 0
    else:
        avgUp = sum(up) / len(up)
    if len(down) == 0:   
        avgDown = 1
    else:
        avgDown = sum(down) / len(down)
   
    RSvalue = avgUp / avgDown
    RSI = 100 - (100 / (1 + RSvalue))
    return RSI



def StoOsc(ticker, DATA, graph):
    DATA['L14'] = DATA['Low'].rolling(window=14).min()
    #Create the "H14" column in the DataFrame
    DATA['H14'] = DATA['High'].rolling(window=14).max()
    #Create the "%K" column in the DataFrame
    DATA['%K'] = 100*((DATA['Close'] - DATA['L14']) / (DATA['H14'] - DATA['L14']) )
    #Create the "%D" column in the DataFrame
    DATA['%D'] = DATA['%K'].rolling(window=3).mean()
    if graph == True:
        fig, axes = plt.subplots(nrows=2, ncols=1,figsize=(15,7))
        DATA['Close'].plot(ax=axes[0]); axes[0].set_title('Close')
        DATA[['%K','%D']].plot(ax=axes[1]); axes[1].set_title('Oscillator')
        plt.title(ticker + " Stochastic Oscillator - 1 Year ")
        # plt.show()
        filename = str(ticker) + "_STO.png"
        fig.savefig(r"Results/%s" %(filename))
    return list(DATA['%K']), list(DATA['%D'])

def MA(ticker, DATA, graph):
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
    if graph == True:
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
        plt.title(ticker + " LMA vs SMA - 1 Year ")
        # plt.show()
        filename = str(ticker) + "_MA.png"
        fig.savefig(r"Results/%s" %(filename))
    return list(signals['positions']), list(signals['short_mavg']), list(signals['long_mavg'])

def Boll(ticker, DATA, graph):
    signals_two = pd.DataFrame(index=DATA.index)
    signals_two['upper_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() + 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
    signals_two['lower_BB'] = DATA['Close'].rolling(window=10, min_periods=1, center=False).mean() - 2 * DATA['Close'].rolling(window=10, min_periods=1, center=False).std()
    if graph == True:
        fig = plt.figure(figsize=(6, 4))
        ax1 = fig.add_subplot(111,  ylabel='Price in $')
        ax = signals_two[['upper_BB', 'lower_BB']].plot(ax=ax1, lw=1, alpha=0.4, color="black")
        ax.fill_between(DATA.index, signals_two['upper_BB'], signals_two['lower_BB'], color='#ADCCFF', alpha=0.4)
        DATA['Close'].plot(ax=ax1, color='r', lw=2.0)
        plt.title(ticker + " Bollinger Band - 1 Year ")

        # plt.show()
        filename = str(ticker) + "_BOLL.png"
        fig.savefig(r"Results/%s" %(filename))
    return list(signals_two['upper_BB']), list(signals_two['lower_BB']), list(DATA['Close'])

def stockVal(ticker, daysBack, graph):
    DATA = pdr.get_data_yahoo(ticker,
                            start = datetime.datetime.today() - timedelta(days=daysBack),
                            end = datetime.datetime.today())   
    Boll_Val = 0
    Sto_Val = 0
    MA_Val = 0
    RSI_Val = 0

    sig, shortMA, longMA = MA(ticker, DATA, graph)
    RSI_v = RSI(ticker, DATA)
    K,D = StoOsc(ticker, DATA, graph)
    up, low, close = Boll(ticker, DATA, graph)

    prev_short = shortMA[0]
    prev_long = longMA[0]
    prev_K = K[0]
    prev_D = D[0]

    if close[-1] > up[-1]:
        Boll_Val = -1
    elif close[-1] < low[-1]:
        Boll_Val = 1

    if RSI_v >= 70:
        RSI_Val = -1 + ((100 - RSI_v) * 0.05)
    elif RSI_v <= 20:
        RSI_Val = 1 - (20 - (RSI_v) * 0.05)
    elif RSI_v >= 50:
        RSI_Val = RSI_v / 100
    else:
        RSI_Val = (RSI_v / 100) * (-1)
    MA_idx = 0
    STO_idx = 0
    for i in range(len(close)):
        if shortMA[i] > longMA[i] and prev_short < prev_long:
            MA_Val = 1
            MA_idx = i
        elif shortMA[i] < longMA[i] and prev_short > prev_long:
            MA_Val = -1
            MA_idx = i
        prev_short = shortMA[i]
        prev_long = longMA[i]

        if K[i] < D[i] and prev_K > prev_D and K[i] >= 80:
            Sto_Val = -1
            STO_idx = i
        elif K[i] > D[i] and prev_K < prev_D and K[i] <= 20:
            Sto_Val = 1
            STO_idx = i
        prev_K = K[i]
        prev_D = D[i]

    if MA_Val == 1:
        MA_Val = MA_Val - ((len(close)-MA_idx) * 0.05)
        if MA_Val < 0:
            MA_Val = 0
    elif MA_Val == -1:
        MA_Val = MA_Val + ((len(close)-MA_idx) * 0.05)
        if MA_Val > 0:
            MA_Val = 0

    if Sto_Val == 1:
        Sto_Val = Sto_Val - ((len(close)-STO_idx) * 0.05)
        if Sto_Val < 0:
            Sto_Val = 0
    elif Sto_Val == -1:
        Sto_Val = Sto_Val + ((len(close)-STO_idx) * 0.05)
        if Sto_Val > 0:
            Sto_Val = 0
    
    # print(Boll_Val, Sto_Val, MA_Val, RSI_Val)
    
    power = Boll_Val + Sto_Val + MA_Val + RSI_Val
    return power





def results(ticker):
    DATA = pdr.get_data_yahoo(ticker,
                            start = datetime.datetime.today() - timedelta(days=500),
                            end = datetime.datetime.today() ) 
    fig = plt.figure(figsize=(6, 4))
    ax1 = fig.add_subplot(111,  ylabel='Price in $')
    DATA['Close'].plot(ax=ax1, color='r', lw=2.0)
    plt.axvline(datetime.datetime(2019, 11, 9))
    plt.title(ticker + " Performance Analysis")
    plt.show()
    filename = str(ticker) + "_ANALYSIS.png"
    fig.savefig(filename)

def create_report(user_email):

    subject = "Automated Stock Report"
    body = "This is an automated email with your in depth stock analytics."
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
    
    filename1 = "FinalAnalysis.pdf"  # In same directory as script\
    filename2 = "recommendedStocks.csv"
    filename3 = "portfolioValues.csv"
    
    # Open PDF file in binary mode
    filepath1 = os.getcwd() + '/Results/' + filename1
    with open(filepath1, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email    
    encoders.encode_base64(part)
    message.attach(part)

    # Add header as key/value pair to attachment part
    part.add_header("Content-Disposition",f"attachment; filename= {filename1}",)

    filepath2 = os.getcwd() + '/Results/' + filename2
    with open(filepath2, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition",f"attachment; filename= {filename2}",)
    message.attach(part)

    filepath3 = os.getcwd() + '/Results/' + filename3
    with open(filepath3, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition",f"attachment; filename= {filename3}",)
    message.attach(part)

     # Add attachment to message and convert message to string
    message.attach(part)
    text = message.as_string()


    
     # Log in to server using secure context and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login("stockanalysis553", password)
        server.sendmail(sender_email, receiver_email, text)
 
def callPDFSaver():
    outputPdfName = "FinalAnalysis"
    pathToSavePdfTo = os.getcwd() + '//' + "Results"
    pathToPictures = os.getcwd() + '//' + "Results"
    splitType = "picture"
    numberOfEntitiesInOnePdf = 120
    listWithImagesExtensions = ["png"]
    picturesAreInRootFolder = True
    nameOfPart = "ALL"
    unite_pictures_into_pdf(outputPdfName, pathToSavePdfTo, pathToPictures, splitType, numberOfEntitiesInOnePdf, listWithImagesExtensions, picturesAreInRootFolder, nameOfPart)

def cleanFolder():
    pathToFolder = os.getcwd() + '//' + "Results"
    files = glob.glob(pathToFolder)
    for f in files:
        os.remove(f)

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def mainUI():
    def extractTickers(t):
        print('extracting...')
        return t.split(',')

    def runProgram():
        print("Email: %s\nStock List: %s" % (e1.get(), e2.get()))
        email = e1.get()
        tickers = extractTickers(e2.get())
        #cleanFolder()

        portfolioDict = {}
        for ticker in tickers:
            power = stockVal(ticker, 365, True)
            print(ticker, ": ", power)
            portfolioDict[ticker] = power

        #make long PDF
        print('saving all images to one PDF...')
        callPDFSaver()
        print('Success!!')
        #get recommendations
        print('Beginning stock recomendations...')
        vals = {}
        file1 = open('recommendations.txt', "r")
        for i,x in enumerate(file1):
            printProgressBar(i,500)
            x = x[2:-3]
            try:
                power = stockVal(x, 365, False)
                vals[x] = power
            except:
                pass
        print('Found our top 10 recomendations!')
        res = dict(sorted(vals.items(), key = itemgetter(1), reverse = True)[:10]) 
        listofDicts = []
        for key in res:
            tmp = {'Ticker' : key , 'Value': res[key] }
            listofDicts.append(tmp)

        portfolioDictList = []
        for key in portfolioDict:
            tmp = {'Ticker' : key , 'Value': portfolioDict[key] }
            portfolioDictList.append(tmp)
           
        recommendedFilename = "recommendedStocks.csv"
        portfolioFilename = "portfolioValues.csv"
        createRecommendationFile(listofDicts, recommendedFilename)
        createRecommendationFile(portfolioDictList, portfolioFilename)


        #send email
        print('sending email...')
        create_report(email)
        print('email sent!')
        sys.exit(0)


    
    master = tk.Tk()
    master.title('Lets make this $$$$$$$')
    master.configure(bg='#4D4E4F')
    master.geometry("500x200")
    tk.Label(master, bg="#4D4E4F", fg="white",
            text="Email:").grid(row=0)
    tk.Label(master, bg="#4D4E4F", fg="white",
            text="List of Tickers: Follow the example.").grid(row=1)

    e1 = tk.Entry(master, bg="#4D4E4F", fg="white")
    v = tk.StringVar(master, value='AAPL,AMZN,TSLA,GE')
    e2 = tk.Entry(master, textvariable = v, bg="#4D4E4F", fg="white")

    e1.grid(row=0, column=1)
    e2.grid(row=1, column=1)


    tk.Button(master, bg="#4D4E4F", fg="black",
            text='Analyze!', command=runProgram).grid(row=3, column=1, sticky=tk.W, pady=4, )

    tk.mainloop()


def createRecommendationFile(dict_data, filename):
    csv_columns = ['Ticker','Value']
    csv_file = os.getcwd() + '/Results/' + filename
    try:
        with open(csv_file, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
            writer.writeheader()
            for data in dict_data:
                writer.writerow(data)
    except IOError:
        print("I/O error")


def main():
    mainUI()

if __name__ == "__main__":
    main()
