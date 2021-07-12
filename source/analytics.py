#data files must be in format Date, [Symbol].Open, [Symbol].High, [Symbol].Low, [Symbol].Close
#datefile as indicated above, must be in CSV format. File itself can be .txt but must at least follow the format
#output file will be written in same format with the indicated statistics following the [Symbol].Close on each line 
#pathToDateFile and pathToOutputFile will be paths starting from inside the source folder
import utility as util
import file_io as io
import plotly.graph_objects as go
from plotly.subplots import make_subplots 
import pandas as pd
from datetime import datetime

class Analytics:
    def __init__(self):

        #import config settings
        #----------------------------------------------------------------------------------
        config = io.fetchJSON("../config.json")["analytics"]
        #set instance variables
        self.SYMBOL = config["SYMBOL"]
        self.PATH_TO_DATA_FILE = config["PATH_TO_DATA_FILE"]
        self.PATH_TO_OUTPUT_FILE = config["PATH_TO_OUTPUT_FILE"]
        #statistics set to true will be written to output file
        self.SIMPLE_MOVING_AVERAGE = config["SIMPLE_MOVING_AVERAGE"]
        self.EXPONENTIAL_MOVING_AVERAGE = config["EXPONENTIAL_MOVING_AVERAGE"]
        #holds the maximum amount of prices to store for calculation
        #should be the minimum needed to calculate all data
        self.QUEUE_MAX_SIZE = config["QUEUE_MAX_SIZE"]
        #True to display a graph of data, False if not
        self.DISPLAY_GRAPH = config["DISPLAY_GRAPH"]
        #toggles whether RSI is calculated or not
        self.SHOW_RSI = config["SHOW_RSI"]
        #RSI calculation period
        self.RSI_PERIOD = config["RSI_PERIOD"]
        #toggles whether RSI upper and lower bounds are drawn to graph
        self.SHOW_RSI_BOUNDS = config["SHOW_RSI_BOUNDS"]
        #RSI overbought and underbought signals
        self.RSI_UPPER = config["RSI_UPPER"]
        self.RSI_LOWER = config["RSI_LOWER"]
        #toggles whether MACD indicator is shown
        self.SHOW_MACD = config["SHOW_MACD"]
        #----------------------------------------------------------------------------------

        #holds the previous QUEUE_MAX_SIZE of close prices
        self.PRICE_QUEUE = []
        #represents current size of PRICE_QUEUE
        self.QUEUE_SIZE = 0
        #holds the previous 9 values of the MACD indicator
        self.MACD_QUEUE = []
        #represents current size of MACD_QUEUE
        self.MACD_QUEUE_SIZE = 0
        #holds current candlestick info
        self.CURRENT_OPEN = 0.0
        self.CURRENT_HIGH = 0.0
        self.CURRENT_LOW = 0.0
        self.CURRENT_CLOSE = 0.0
        self.CURRENT_VOLUME = 0.0
        #holds the previous EMA entries
        self.PREVIOUS_EMA_DATA = {}
        self.setUpPreviousEMAData()
        #holds next entry to output file
        self.NEXT_ENTRY = ""
    
    #sets up PREVIOUS_EMA_DATA using data from config
    def setUpPreviousEMAData(self):
        for i in range(len(self.EXPONENTIAL_MOVING_AVERAGE)):
            self.PREVIOUS_EMA_DATA["EMA" + str(self.EXPONENTIAL_MOVING_AVERAGE[i])] = 0.0
        if (self.SHOW_MACD):
            self.PREVIOUS_EMA_DATA["MACDEMA"] = 0.0
            self.PREVIOUS_EMA_DATA["EMA12"] = 0.0
            self.PREVIOUS_EMA_DATA["EMA26"] = 0.0

    #manages the price queue array
    def updatePriceQueue(self):
        if (self.QUEUE_SIZE < self.QUEUE_MAX_SIZE):
            self.PRICE_QUEUE.insert(0, self.CURRENT_CLOSE)
        else:
            self.PRICE_QUEUE.pop( (self.QUEUE_MAX_SIZE - 1) )
            self.PRICE_QUEUE.insert(0, self.CURRENT_CLOSE)
        if (self.QUEUE_SIZE < self.QUEUE_MAX_SIZE):
            self.QUEUE_SIZE += 1

    #returns the simple moving average of period
    def getSimpleMovingAverage(self, period):
        if (period > self.QUEUE_SIZE): return 0.0
        sum_ = 0.0
        for i in range(period):
            sum_ += self.PRICE_QUEUE[i]
        return sum_ / period

    #returns the exponential moving average of period
    def getExponentialMovingAverage(self, period):
        previousEMA = self.PREVIOUS_EMA_DATA["EMA" + str(period)]
        if (period + 1 > self.QUEUE_SIZE): return 0.0
        if (previousEMA == 0.0):
            previousEMA = self.getSimpleMovingAverage(period)
        k = (2 / (period + 1))
        newEMA = k * (self.PRICE_QUEUE[0] - previousEMA) + previousEMA
        self.PREVIOUS_EMA_DATA["EMA" + str(period)] = newEMA
        return newEMA

    #returns the RSI 
    def getRSI(self):
        if (self.QUEUE_SIZE > self.RSI_PERIOD):
            gainSum = 0
            lossSum = 0
            for i in range(self.RSI_PERIOD):
                change = self.PRICE_QUEUE[i] - self.PRICE_QUEUE[i+1]
                if (change > 0): gainSum += change
                else: lossSum += abs(change)
            gainAvg = gainSum / self.RSI_PERIOD
            lossAvg = lossSum / self.RSI_PERIOD
            _rs = gainAvg / lossAvg
            newRSI = 100 - (100/(1+_rs))
            newRSI = round(newRSI, 2)
            return newRSI
        return 0.0

    #returns the MACD indicator
    def getMACD(self):
        period12EMA = self.getExponentialMovingAverage(12)
        period26EMA = self.getExponentialMovingAverage(26)
        if(period12EMA == 0.0 or period26EMA == 0.0): return 0.0
        newMACD = period12EMA - period26EMA
        if (self.MACD_QUEUE_SIZE < 9):
            self.MACD_QUEUE.insert(0, newMACD)
        else:
            self.MACD_QUEUE.pop(8)
            self.MACD_QUEUE.insert(0, newMACD)
        if (self.MACD_QUEUE_SIZE < 9):
            self.MACD_QUEUE_SIZE += 1
        return newMACD

    #returns the MACD signal indicator
    def getMACDSignal(self):
        previousEMA = self.PREVIOUS_EMA_DATA["MACDEMA"]
        if (self.MACD_QUEUE_SIZE < 9): return 0.0
        k = (2 / (10))
        newEMA = k * (self.MACD_QUEUE[0] - previousEMA) + previousEMA
        self.PREVIOUS_EMA_DATA["MACDEMA"] = newEMA
        return newEMA

    #appends custom list of SMA statistic data to next entry in a formatted string
    def appendSMA(self):
        customSMAData = ""
        for i in range(len(self.SIMPLE_MOVING_AVERAGE)):
            newSMA = round(self.getSimpleMovingAverage(self.SIMPLE_MOVING_AVERAGE[i]), 2)
            customSMAData += ("," + str(newSMA))
        self.NEXT_ENTRY += customSMAData

    #appends custom list of EMA statistic data to next entry in a formatted string  
    def appendEMA(self):
        customEMAData = ""
        for i in range(len(self.EXPONENTIAL_MOVING_AVERAGE)):
            newEMA = round(self.getExponentialMovingAverage(self.EXPONENTIAL_MOVING_AVERAGE[i]), 2)
            customEMAData += ("," + str(newEMA))
        self.NEXT_ENTRY += customEMAData

    #appends RSI data to next entry in formatted string
    def appendRSI(self):
        if (self.SHOW_RSI):
            newRSI = self.getRSI()
            self.NEXT_ENTRY += ("," + str(newRSI)) 
            if (self.SHOW_RSI_BOUNDS): self.NEXT_ENTRY += ("," + str(self.RSI_UPPER) + ".0," + str(self.RSI_LOWER) + ".0")

    #appends MACD, signal, and histogram to next entry in formatted string
    def appendMACD(self):
        if (self.SHOW_MACD):
            newMACD = round(self.getMACD(), 2)
            if (newMACD == 0.0):
                self.NEXT_ENTRY += (",0.0,0.0,0.0")
                return
            newMACDSignal = round(self.getMACDSignal(), 2)
            newMACDHist = round((newMACD - newMACDSignal), 2)
            if (newMACDSignal == 0.0): newMACDHist = 0.0
            self.NEXT_ENTRY += ("," + str(newMACD) + "," + str(newMACDSignal) + "," + str(newMACDHist))

    #gets the custom statistic header string for the output file
    def getStatisticHeaderString(self):
        #will hold current custom header message
        customHeader = ""
        #appends all necessary header info for simple moving average
        for i in range(len(self.SIMPLE_MOVING_AVERAGE)):
            customHeader += (",SMA" + str(self.SIMPLE_MOVING_AVERAGE[i]))
        #appends all necessary header info for exponential moving average
        for i in range(len(self.EXPONENTIAL_MOVING_AVERAGE)):
            customHeader += (",EMA" + str(self.EXPONENTIAL_MOVING_AVERAGE[i]))
        #append RSI indicator column
        if(self.SHOW_RSI): 
            customHeader += ",RSI"
            if(self.SHOW_RSI_BOUNDS): customHeader += ",RSIU,RSIL"
        #append MACD indicator column
        if(self.SHOW_MACD):
            customHeader += ",MACD,MACDSig,MACDHist"
        return customHeader

    #runs analytics module, produces graph
    def run(self):
        #create custom header message for output file and write to outputfile
        headerMessage = 'Date,{}.Open,{}.High,{}.Low,{}.Close,Volume'.format(self.SYMBOL,self.SYMBOL,self.SYMBOL,self.SYMBOL)
        headerMessage += self.getStatisticHeaderString()
        io.writeToFile(self.PATH_TO_OUTPUT_FILE, headerMessage)

        #open the data file in read mode and split by lines
        dataFile = open(self.PATH_TO_DATA_FILE, 'r')
        Lines = dataFile.readlines()

        #for every line of data
        for line in Lines:
            #split by comma
            data = line.split(',')
            #make global data
            self.CURRENT_OPEN = round(float(data[1].strip()), 2)
            self.CURRENT_HIGH = round(float(data[2].strip()), 2)
            self.CURRENT_LOW = round(float(data[3].strip()), 2)
            self.CURRENT_CLOSE = round(float(data[4].strip()), 2)
            self.CURRENT_VOLUME = round(float(data[5].strip()), 2)
            #update price queue
            self.updatePriceQueue()
            #add date and candlestick data to next entry
            self.NEXT_ENTRY += '{},{},{},{},{}'.format(
                data[0],
                self.CURRENT_OPEN,
                self.CURRENT_HIGH,
                self.CURRENT_LOW,
                self.CURRENT_CLOSE)
            #add current volume to next entry
            self.NEXT_ENTRY += ',' + str(self.CURRENT_VOLUME)
            #append all simple moving average data to next entry
            self.appendSMA()
            #append all exponential moving average data to next entry
            self.appendEMA()
            #append RSI data
            self.appendRSI()
            #append MACD data
            self.appendMACD()
            #append next entry to output file
            io.appendToFile(self.PATH_TO_OUTPUT_FILE, self.NEXT_ENTRY)
            #clear next entry
            self.NEXT_ENTRY = ""
        
        #display graph is set to true
        if (self.DISPLAY_GRAPH): self.displayGraph()
        
    #display a graph of data
    def displayGraph(self):
        #read csv file created by analytics module
        df = pd.read_csv(self.PATH_TO_OUTPUT_FILE)

        #create and show first chart
        #----------------------------------------------------------------------------------
        #this chart will display candlestick, RSI, and MACD
        fig1 = make_subplots(
        rows=3, 
        cols=1, 
        subplot_titles=( (self.SYMBOL + " Candlestick" ), "RSI", "MACD"))
        #create candlestick chart using with x being Date, and the candlesticks made using AAPL.Open, AAPL.High, AAPL.Low, AAPL.Close
        fig1.append_trace(
            go.Candlestick(x=df['Date'],
                open=df[(self.SYMBOL + '.Open')],
                high=df[(self.SYMBOL + '.High')],
                low=df[(self.SYMBOL + '.Low')],
                close=df[(self.SYMBOL + '.Close')],
                name=(self.SYMBOL + ' Candle')
                        ),row=1, col=1)
        fig1.update_xaxes(row=1, col=1, rangeslider_visible=False)
        #adds RSI indicator and overbought and underbought signals
        if (self.SHOW_RSI):
            #add RSI indicator data
            fig1.append_trace(go.Scatter(x=df['Date'], y=df["RSI"], text="RSI", name="RSI", line=dict(color='rgb(0, 0, 0)')), row=2, col=1)
            if (self.SHOW_RSI_BOUNDS):
                #add RSI overbought and under bought signals
                fig1.append_trace(go.Scatter(x=df['Date'], y=df["RSIU"], text="RSI Overbought Signal", name="RSI Overbought Signal", line=dict(color='rgb(255, 0, 0)')), row=2, col=1)
                fig1.append_trace(go.Scatter(x=df['Date'], y=df["RSIL"], text="RSI Underbought Signal", name="RSI Underbought Signal", line=dict(color='rgb(0, 128, 0)')), row=2, col=1)
        #adds MACD indicator
        if (self.SHOW_MACD):
            fig1.append_trace(go.Scatter(x=df['Date'], y=df["MACD"], text="MACD", name="MACD", line=dict(color='rgb(0, 128, 0)')), row=3, col=1)
            fig1.append_trace(go.Scatter(x=df['Date'], y=df["MACDSig"], text="MACD Signal", name="MACD Signal", line=dict(color='rgb(255, 0, 0)')), row=3, col=1)
            fig1.append_trace(go.Bar(x=df['Date'], y=df["MACDHist"], text="MACD Histogram", name="MACD Histogram"), row=3, col=1)
        #show plot, opens in browser
        fig1.show()
        #----------------------------------------------------------------------------------

        #create and show second chart
        #----------------------------------------------------------------------------------
        #this chart will display SMA, EMA, and Volume
        fig2 = make_subplots(
        rows=3, 
        cols=1, 
        subplot_titles=( "SMA", "EMA", "Volume"))
        #adds SMA statistic data
        for i in range(len(self.SIMPLE_MOVING_AVERAGE)):
            title = 'SMA' + str(self.SIMPLE_MOVING_AVERAGE[i])
            #add SMA5 scatter plot with x being date, and SMA5 being y
            fig2.append_trace(go.Scatter(x=df['Date'], y=df[title], text=title, name=title), row=1, col=1)
        #adds EMA statistic data
        for i in range(len(self.EXPONENTIAL_MOVING_AVERAGE)):
            title = 'EMA' + str(self.EXPONENTIAL_MOVING_AVERAGE[i])
            #add SMA5 scatter plot with x being date, and SMA5 being y
            fig2.append_trace(go.Scatter(x=df['Date'], y=df[title], text=title, name=title), row=2, col=1)
        #adds volume statistic data
        fig2.append_trace(go.Bar(x=df['Date'], y=df["Volume"], text="Volume", name="Volume"), row=3, col=1)
        #----------------------------------------------------------------------------------
        
        #show plot, opens in browser
        fig2.show()