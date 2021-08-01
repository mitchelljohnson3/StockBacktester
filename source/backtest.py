import file_io as io
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


class Backtest:
    def __init__(self):
        self.config = io.fetchJSON("../config.json")["backtest"]
        self.JUST_GRAPH = self.config["JUST_GRAPH"]
        self.PATH_TO_HISTORY_FILE = self.config["PATH_TO_HISTORY_FILE"]
        self.PATH_TO_RESULTS_FILE = self.config["PATH_TO_RESULTS_FILE"]
        self.PATH_TO_DATA_FILE = self.config["PATH_TO_DATA_FILE"]
        self.DISPLAY_RESULTS_GRAPH = self.config["DISPLAY_RESULTS_GRAPH"]
        self.USE_CANDLESTICK_ON_RESULTS_GRAPH = self.config["USE_CANDLESTICK_ON_RESULTS_GRAPH"]
        self.SYMBOL = self.config["SYMBOL"]
        self.CASH = self.config["CASH"]
        self.QUANTITY = 0
        self.TOTAL_FUNDS_INVESTED = 0.0
        self.AVERAGE_SHARE_PRICE = 0.0
        self.SUCCESSFUL_TRADES = 0
        self.FAILED_TRADES = 0
        self.DATA = {
            "CURRENT_DATE": "",
            "CURRENT_OPEN": 0.0,
            "CURRENT_HIGH": 0.0,
            "CURRENT_LOW": 0.0,
            "CURRENT_CLOSE": 0.0,
            "CURRENT_VOLUME": 0
        }
        self.PREVIOUS_DATA = {
            "PREVIOUS_DATE": "",
            "PREVIOUS_OPEN": 0.0,
            "PREVIOUS_HIGH": 0.0,
            "PREVIOUS_LOW": 0.0,
            "PREVIOUS_CLOSE": 0.0,
            "PREVIOUS_VOLUME": 0
        }
        self.BUY_JUST_OCCURRED = False
        self.SELL_JUST_OCCURRED = False

    # adds custom data fields to self.DATA
    def readHeader(self, header):
        header_elements = header.split(',')
        for i in range(len(header_elements)):
            if (i > 5):
                self.DATA[header_elements[i]] = 0.0

    # updates self.DATA to contain current stock and indicator information
    def update(self, data):
        self.BUY_JUST_OCCURRED = False
        self.SELL_JUST_OCCURRED = False
        data_elements = data.split(',')
        data_keys = list(self.DATA.keys())
        # copy over self.DATA to self.PREVIOUS_DATA
        for i in range(len(data_elements)):
            self.PREVIOUS_DATA[data_keys[i]] = self.DATA[data_keys[i]]
        # update self.DATA with new data
        for i in range(len(data_elements)):
            if (i == 0):
                self.DATA[data_keys[i]] = data_elements[i]
            else:
                self.DATA[data_keys[i]] = float(data_elements[i])

    # runs the backtest
    def run(self):
        # if JUST_GRAPH is true, don't bother calculating, just display whats in the file already
        if (self.JUST_GRAPH and self.DISPLAY_RESULTS_GRAPH):
            self.displayGraph()
            return
        # if a new graph is to be displayed, overwrite the previous runs data
        if (self.DISPLAY_RESULTS_GRAPH):
            self.setupResultsHeader()
        # clear the order history file
        io.writeToFile(self.PATH_TO_HISTORY_FILE, "")
        df = io.readFile(self.PATH_TO_DATA_FILE).readlines()
        self.readHeader(df[0])
        for i in range(1, len(df)):
            # update with new data
            self.update(df[i])

            # call the algorithm
            # <><><><><><><><><><><><><><><><><><>
            # self.simpleMovingAverageCrossover()
            self.bunk()
            #self.RSIThresholdCrossover()
            # self.MACDandRSI()
            # <><><><><><><><><><><><><><><><><><>

            # appends results to results file
            if (self.DISPLAY_RESULTS_GRAPH):
                self.addToResults()

        # id self.DISPLAY_RESULTS_GRAPH is true, display results graph
        if (self.DISPLAY_RESULTS_GRAPH):
            self.displayGraph()
        # else print results statement to console
        remaining_assets = self.CASH + \
            (self.QUANTITY * self.DATA["CURRENT_CLOSE"])
        total_trades = self.SUCCESSFUL_TRADES + self.FAILED_TRADES
        success_percentage = round(
            ((self.SUCCESSFUL_TRADES / total_trades) * 100), 2)
        starting_funds = self.config["CASH"]
        percentage_gain = round(((self.CASH / starting_funds) * 100) - 100, 2)
        print("------------------------------------------")
        print("Assets Remaining: " + str(round(remaining_assets, 2)))
        print("Cash Remaining: " + str(round(self.CASH, 2)))
        print("Successful Trades: " + str(self.SUCCESSFUL_TRADES) +
              " Failed Trades: " + str(self.FAILED_TRADES))
        print("Success Percentage: %" + str(success_percentage))
        print("Percantage Gain: %" + str(percentage_gain))
        print("Quantity Remaining: " + str(self.QUANTITY))
        print("------------------------------------------")

    # adds orders to history
    def orderSuccess(self, quantity, BUYorSELL, GAINorLOSS):
        data = ""
        if (BUYorSELL):
            data = '{} | Bought {} of {} at {} - Average Share Price: {}'.format(
                self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"], self.AVERAGE_SHARE_PRICE)
            self.BUY_JUST_OCCURRED = True
        else:
            data = '{} | Sold {} of {} at {} - Average Share Price: {}'.format(
                self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"], self.AVERAGE_SHARE_PRICE)
            if (GAINorLOSS):
                data += ' --> GAIN'
            else:
                data += ' --> LOSS'
            self.SELL_JUST_OCCURRED = True
        io.appendToFile(self.PATH_TO_HISTORY_FILE, data)

    # adds failed orders to history
    def orderFailed(self, quantity, BUYorSELL):
        data = ""
        if (BUYorSELL):
            data = '{} | Failed to buy {} of {} at {}'.format(
                self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"])
        else:
            data = '{} | Failed to Sell {} of {} at {}'.format(
                self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"])
        io.appendToFile(self.PATH_TO_HISTORY_FILE, data)

    # buys quantity of symbol
    def buy(self, quantity):
        if(quantity == 0):
            return
        # if not enough money to complete buy order
        if (self.fundsAvailable(quantity) == False):
            self.orderFailed(quantity, True)
            return

        # process buy
        funds_required = quantity * self.DATA["CURRENT_CLOSE"]
        self.TOTAL_FUNDS_INVESTED += funds_required
        self.QUANTITY += quantity
        self.AVERAGE_SHARE_PRICE = round(
            (self.TOTAL_FUNDS_INVESTED / self.QUANTITY), 2)
        self.CASH -= funds_required
        self.orderSuccess(quantity, True, False)

    # sells quantity of symbol
    def sell(self, quantity):
        if(quantity == 0):
            return
        # if not enough shares to complete sell order
        if (self.sharesAvailable(quantity) == False):
            self.orderFailed(quantity, False)
            return

        # determine whether the trade was successful or not
        successOrFail = False
        if (self.DATA["CURRENT_CLOSE"] >= self.AVERAGE_SHARE_PRICE):
            self.SUCCESSFUL_TRADES += 1
            successOrFail = True
        else:
            self.FAILED_TRADES += 1

        # process sell
        funds_returned = quantity * self.DATA["CURRENT_CLOSE"]
        self.QUANTITY -= quantity
        if (self.QUANTITY == 0):
            self.TOTAL_FUNDS_INVESTED = 0
        else:
            self.TOTAL_FUNDS_INVESTED = (
                self.QUANTITY * self.AVERAGE_SHARE_PRICE)
        if (self.QUANTITY != 0):
            self.AVERAGE_SHARE_PRICE = round(
                (self.TOTAL_FUNDS_INVESTED / self.QUANTITY), 2)
        else:
            self.AVERAGE_SHARE_PRICE = 0.0
        self.CASH += funds_returned
        self.orderSuccess(quantity, False, successOrFail)

    # returns true if enough funds are available to buy quantity of symbol at price
    def fundsAvailable(self, quantity):
        funds_required = quantity * self.DATA["CURRENT_CLOSE"]
        if (funds_required <= self.CASH):
            return True
        return False

    # returns true if number of shares are available to be sold
    def sharesAvailable(self, quantity):
        if (quantity <= self.QUANTITY):
            return True
        return False

    # buys as many shares as possible
    def allIn(self):
        maxShares = int(self.CASH / self.DATA["CURRENT_CLOSE"])
        self.buy(maxShares)

    # sells all shares
    def allOut(self):
        self.sell(self.QUANTITY)

    # returns True if a buy just occurred

    # creates results header line
    def setupResultsHeader(self):
        headerMessage = 'Date,{}.Open,{}.High,{}.Low,{}.Close,Assets,BUY,SELL'.format(
            self.SYMBOL, self.SYMBOL, self.SYMBOL, self.SYMBOL)
        io.writeToFile(self.PATH_TO_RESULTS_FILE, headerMessage)

    # appends single line to backtest results file
    def addToResults(self):
        currentAssets = round(
            (self.CASH + (self.QUANTITY * self.DATA["CURRENT_CLOSE"])), 2)
        buyValue = "---"
        sellValue = "---"
        if (self.BUY_JUST_OCCURRED):
            buyValue = self.DATA["CURRENT_CLOSE"]
        if (self.SELL_JUST_OCCURRED):
            sellValue = self.DATA["CURRENT_CLOSE"]
        next_entry = '{},{},{},{},{},{},{},{}'.format(
            self.DATA["CURRENT_DATE"],
            self.DATA["CURRENT_OPEN"],
            self.DATA["CURRENT_HIGH"],
            self.DATA["CURRENT_LOW"],
            self.DATA["CURRENT_CLOSE"],
            currentAssets,
            buyValue,
            sellValue)
        io.appendToFile(self.PATH_TO_RESULTS_FILE, next_entry)

    # displays results graph
    def displayGraph(self):
        # read csv file created by backtest module
        df = pd.read_csv(self.PATH_TO_RESULTS_FILE)

        # create figure that will have 2 rows and 1 column. first graph will be the candlestick chart with buy and sell signals
        # second graph will be total assets over time
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=((self.SYMBOL + " Candlestick + Buy & Sell Signals"), "Total Assets"))

        if (self.USE_CANDLESTICK_ON_RESULTS_GRAPH):
            # create candlestick chart using with x being Date, and the candlesticks made using AAPL.Open, AAPL.High, AAPL.Low, AAPL.Close
            fig.append_trace(
                go.Candlestick(x=df['Date'],
                               open=df[(self.SYMBOL + '.Open')],
                               high=df[(self.SYMBOL + '.High')],
                               low=df[(self.SYMBOL + '.Low')],
                               close=df[(self.SYMBOL + '.Close')],
                               name=(self.SYMBOL + ' Candle')
                               ), row=1, col=1)
            fig.update_xaxes(row=1, col=1, rangeslider_visible=False)
        else:
            # create a simple scatter plot of price using current_close
            fig.append_trace(go.Scatter(x=df['Date'], y=df[(
                self.SYMBOL + '.Close')], text="Price", name="Price", line=dict(color='rgb(0, 0, 0)')), row=1, col=1)

        # append buy and sell signals
        # .....
        fig.append_trace(go.Scatter(x=df['Date'], y=df['BUY'], mode='markers',
                         text="BUY", name="BUY", line=dict(color='rgb(0, 128, 0)')), row=1, col=1)
        fig.append_trace(go.Scatter(x=df['Date'], y=df['SELL'], mode='markers',
                         text="SELL", name="SELL", line=dict(color='rgb(255, 0, 0)')), row=1, col=1)

        # create total assets over time graph
        fig.append_trace(go.Scatter(x=df['Date'], y=df["Assets"], text="Assets", name="Assets", line=dict(
            color='rgb(0, 0, 0)')), row=2, col=1)

        # display graph
        fig.show()

    # -------------------------------------------------------------------------------------------------------------------------------------
    # below are functions that help in writing investment strategy functions
    # indicator_1 and indicator_2 are string representations of the indicator. Ex: "SMA5", or "RSI", or "MACD"

    # returns True in the event of indicator_1 crossing ABOVE indicator_2
    def crossesOver(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0):
            return False
        indicator_1_above_indicator_2 = self.DATA[indicator_1] > self.DATA[indicator_2]
        crossover_just_occurred = self.PREVIOUS_DATA[indicator_1] < self.PREVIOUS_DATA[indicator_2]
        return (indicator_1_above_indicator_2 and crossover_just_occurred)

    # returns True in the event of indicator_1 crossing BELOW indicator_2
    def crossesBelow(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0):
            return False
        indicator_1_below_indicator_2 = self.DATA[indicator_1] < self.DATA[indicator_2]
        crossover_just_occurred = self.PREVIOUS_DATA[indicator_1] > self.PREVIOUS_DATA[indicator_2]
        return (indicator_1_above_indicator_2 and crossover_just_occurred)

    # returns True if indicator_1 is currently ABOVE indicator_2
    def isAbove(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0):
            return False
        indicator_1_above_indicator_2 = self.DATA[indicator_1] > self.DATA[indicator_2]
        return indicator_1_above_indicator_2

    # returns True if indicator_1 is currently BELOW indicator_2
    def isBelow(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0):
            return False
        indicator_1_below_indicator_2 = self.DATA[indicator_1] < self.DATA[indicator_2]
        return indicator_1_below_indicator_2

    # returns True if indicator_1 is currently ABOVE value. value is a number
    def isAboveValue(self, indicator_1, value):
        if (self.DATA[indicator_1] == 0.0):
            return False
        indicator_1_above_value = self.DATA[indicator_1] > value
        return indicator_1_above_value

    # returns True if indicator_1 is currently BELOW value. value is a number
    def isBelowValue(self, indicator_1, value):
        if (self.DATA[indicator_1] == 0.0):
            return False
        indicator_1_below_value = self.DATA[indicator_1] < value
        return indicator_1_below_value

    # -------------------------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------------------------------------------------------
    # Below is where different investment strategies will be defined
    # -------------------------------------------------------------------------------------------------------------------------------------
    # -------------------------------------------------------------------------------------------------------------------------------------

    # this strategy simply buys when the SMA5 crosses above the SMA20 and sells when the SMA20 crosses above the SMA5
    def simpleMovingAverageCrossover(self):
        if (self.crossesOver("SMA5", "SMA20")):
            self.allIn()
        if (self.crossesOver("SMA20", "SMA5")):
            self.allOut()

    # -------------------------------------------------
    # -------------------------------------------------
    # tested with 1 min and daily chart, avg of %70 success rate
    # -------------------------------------------------
    # -------------------------------------------------
    # buys when RSI crosses under underbought signal, and sells when RSI crosses overbought signal

    def RSIThresholdCrossover(self):
        if (self.crossesOver("RSI", "RSIL") and self.isAbove("MACDSig", "MACD")):
            self.allIn()
        if (self.crossesOver("RSIU", "RSI") or self.isAboveValue("RSI", 65)):
            self.allOut()

    def bunk(self):
        if (self.crossesOver("MACD", "MACDSig")):
            self.allIn()
        if (self.crossesOver("MACDSig", "MACD")):
            self.allOut()

    # MACD and RSI crossover
    def MACDandRSI(self):
        if (self.crossesOver("MACD", "MACDSig") and self.isBelowValue("RSI", 30)):
            self.allIn()
        if (self.crossesOver("MACDSig", "MACD") and self.isAboveValue("RSI", 70)):
            self.allOut()
