import file_io as io

class Backtest:
    def __init__(self):
        config = io.fetchJSON("../config.json")["backtest"]
        self.DUMP_REMAINING_ASSETS = config["DUMP_REMAINING_ASSETS"]
        self.PATH_TO_HISTORY_FILE = config["PATH_TO_HISTORY_FILE"]
        self.PATH_TO_RESULTS_FILE = config["PATH_TO_RESULTS_FILE"]
        self.PATH_TO_DATA_FILE = config["PATH_TO_DATA_FILE"]
        self.SYMBOL = config["SYMBOL"]
        self.BUDGET = config["BUDGET"]
        self.QUANTITY = 0
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
    
    #adds custom data fields to self.DATA
    def readHeader(self, header):
        header_elements = header.split(',')
        for i in range(len(header_elements)):
            if (i > 5):
                self.DATA[header_elements[i]] = 0.0
    
    #updates self.DATA to contain current stock and indicator information
    def update(self, data):
        data_elements = data.split(',')
        data_keys = list(self.DATA.keys())
        #copy over self.DATA to self.PREVIOUS_DATA
        for i in range(len(data_elements)):
            self.PREVIOUS_DATA[data_keys[i]] = self.DATA[data_keys[i]]
        #update self.DATA with new data
        for i in range(len(data_elements)):
            if (i == 0): self.DATA[data_keys[i]] = data_elements[i]
            else: self.DATA[data_keys[i]] = float(data_elements[i])
                
    #runs the backtest
    def run(self):
        #clear the order history file
        io.writeToFile(self.PATH_TO_HISTORY_FILE, "")
        df = io.readFile(self.PATH_TO_DATA_FILE).readlines()
        self.readHeader(df[0])
        for i in range(1, len(df)):
            self.update(df[i])
            #call the algorithm
            #<><><><><><><><><><><><><><><><><><>
            # self.simpleMovingAverageCrossover()
            #self.RSIThresholdCrossover()
            self.MACDandRSI()
            #<><><><><><><><><><><><><><><><><><>

        #sell off remaining shares if any remain and DUMP_REMAINING_ASSETS is true
        if (self.DUMP_REMAINING_ASSETS): self.sell(self.QUANTITY)

        #print backtest results statement
        remaining_assets = self.BUDGET + (self.QUANTITY * self.DATA["CURRENT_CLOSE"])
        print("------------------------------------------")
        print("Assets Remaining: " + str(round(remaining_assets, 2)))
        print("Cash Remaining: " + str(round(self.BUDGET, 2)))
        print("Quantity Remaining: " + str(self.QUANTITY))
        print("------------------------------------------")

    #adds orders to history
    def orderSuccess(self, quantity, BUYorSELL):
        data = ""
        if (BUYorSELL): data = '{} | Bought {} of {} at {}'.format(self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"])
        else: data = '{} | Sold {} of {} at {}'.format(self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"])
        io.appendToFile(self.PATH_TO_HISTORY_FILE, data)

    #adds failed orders to history
    def orderFailed(self, quantity, BUYorSELL):
        data = ""
        if (BUYorSELL): data = '{} | Failed to buy {} of {} at {}'.format(self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"])
        else: data = '{} | Failed to sell {} of {} at {}'.format(self.DATA["CURRENT_DATE"], quantity, self.SYMBOL, self.DATA["CURRENT_CLOSE"])
        io.appendToFile(self.PATH_TO_HISTORY_FILE, data)

    #buys quantity of symbol
    def buy(self, quantity):
        if(quantity == 0): return
        #if not enough money to complete buy order
        if (not self.fundsAvailable(quantity)): 
            self.orderFailed(quantity, True)
            return
        #process buy
        funds_required = quantity * self.DATA["CURRENT_CLOSE"]
        self.QUANTITY += quantity
        self.BUDGET -= funds_required
        self.orderSuccess(quantity, True)
        
    #sells quantity of symbol
    def sell(self, quantity):
        if(quantity == 0): return
        #if not enough shares to complete sell order
        if (not self.sharesAvailable(quantity)):
            self.orderFailed(quantity, False)
            return
        #process sell
        funds_returned = quantity * self.DATA["CURRENT_CLOSE"]
        self.QUANTITY -= quantity
        self.BUDGET += funds_returned
        self.orderSuccess(quantity, False)

    #returns true if enough funds are available to buy quantity of symbol at price
    def fundsAvailable(self, quantity):
        funds_required = quantity * self.DATA["CURRENT_CLOSE"]
        if (funds_required <= self.BUDGET): return True
        return False

    #returns true if number of shares are available to be sold
    def sharesAvailable(self, quantity):
        if (quantity <= self.QUANTITY): return True
        return False

    #buys as many shares as possible
    def allIn(self):
        maxShares = int(self.BUDGET / self.DATA["CURRENT_CLOSE"])
        self.buy(maxShares)
    #sells all shares
    def allOut(self):
        self.sell(self.QUANTITY)

    #-------------------------------------------------------------------------------------------------------------------------------------
    #below are functions that help in writing investment strategy functions
    #indicator_1 and indicator_2 are string representations of the indicator. Ex: "SMA5", or "RSI", or "MACD"

    #returns True in the event of indicator_1 crossing ABOVE indicator_2
    def crossesOver(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0): return False
        indicator_1_above_indicator_2 = self.DATA[indicator_1] > self.DATA[indicator_2]
        crossover_just_occurred = self.PREVIOUS_DATA[indicator_1] < self.PREVIOUS_DATA[indicator_2]
        return (indicator_1_above_indicator_2 and crossover_just_occurred)

    #returns True in the event of indicator_1 crossing BELOW indicator_2
    def crossesBelow(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0): return False
        indicator_1_below_indicator_2 = self.DATA[indicator_1] < self.DATA[indicator_2]
        crossover_just_occurred = self.PREVIOUS_DATA[indicator_1] > self.PREVIOUS_DATA[indicator_2]
        return (indicator_1_above_indicator_2 and crossover_just_occurred)

    #returns True if indicator_1 is currently ABOVE indicator_2
    def isAbove(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0): return False
        indicator_1_above_indicator_2 = self.DATA[indicator_1] > self.DATA[indicator_2]
        return indicator_1_above_indicator_2

    #returns True if indicator_1 is currently BELOW indicator_2
    def isBelow(self, indicator_1, indicator_2):
        if (self.DATA[indicator_1] == 0.0 or self.DATA[indicator_2] == 0.0): return False
        indicator_1_below_indicator_2 = self.DATA[indicator_1] < self.DATA[indicator_2]
        return indicator_1_below_indicator_2

    #returns True if indicator_1 is currently ABOVE value. value is a number
    def isAboveValue(self, indicator_1, value):
        if (self.DATA[indicator_1] == 0.0): return False
        indicator_1_above_value = self.DATA[indicator_1] > value
        return indicator_1_above_value

    #returns True if indicator_1 is currently BELOW value. value is a number
    def isBelowValue(self, indicator_1, value):
        if (self.DATA[indicator_1] == 0.0): return False
        indicator_1_below_value = self.DATA[indicator_1] < value
        return indicator_1_below_value

    #-------------------------------------------------------------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------------------------------------------------------------
    #Below is where different investment strategies will be defined
    #-------------------------------------------------------------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------------------------------------------------------------
    
    #this strategy simply buys when the SMA5 crosses above the SMA20 and sells when the SMA20 crosses above the SMA5
    def simpleMovingAverageCrossover(self):
        if (self.crossesOver("SMA5", "SMA20")):
            self.allIn()
        if (self.crossesOver("SMA20", "SMA5")):
            self.allOut()

    #buys when RSI crosses under underbought signal, and sells when RSI crosses overbought signal
    def RSIThresholdCrossover(self):
        if (self.crossesOver("RSIL", "RSI")):
            self.buy(50)
        if (self.crossesOver("RSI", "RSIU")):
            self.sell(50)

    #MACD and RSI crossover
    def MACDandRSI(self):
        if (self.crossesOver("MACD", "MACDSig") and self.isBelowValue("RSI", 30)):
            self.allIn()
        if (self.crossesOver("MACDSig", "MACD") and self.isAboveValue("RSI", 70)):
            self.allOut()