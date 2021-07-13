import file_io as io
import sys
sys.path.append("..")
from strategies.simpleMovingAverageCrossover import simpleMovingAverageCrossover

class Backtest:
    def __init__(self):
        config = io.fetchJSON("../config.json")["backtest"]
        self.PATH_TO_HISTORY_FILE = config["PATH_TO_HISTORY_FILE"]
        self.PATH_TO_PORTFOLIO_FILE = config["PATH_TO_PORTFOLIO_FILE"]
        self.PATH_TO_DATA_FILE = config["PATH_TO_DATA_FILE"]
        self.SYMBOL = config["SYMBOL"]
        self.DATA = {
            "CURRENT_DATE": "",
            "CURRENT_OPEN": 0.0,
            "CURRENT_HIGH": 0.0,
            "CURRENT_LOW": 0.0,
            "CURRENT_CLOSE": 0.0,
            "CURRENT_VOLUME": 0
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
        data_keys = self.DATA.keys()
        for i in range(len(data_elements)):
            if (i == 0): self.DATA[data_keys[i]] = data_elements[i]
            else if (i == 5): self.DATA[data_keys[i]] = int(data_elements[i])
            else: self.DATA[data_keys[i]] = double(data_elements[i])
                
    #runs the backtest
    def run(self):
        df = io.readFile(self.PATH_TO_DATA_FILE)
        self.readHeader(df[0])
        for i in range(1, len(df)):
            self.update(df[i])
            #call the algorithm

    #adds orders to history
    def addToHistory(symbol, quantity, price, date):
        io.writeToTXTFile(self.PATH_TO_HISTORY_FILE, data)

    #adds a quantity of symbol to portfolio.json
    def addToPortfolio(symbol, quantity, price):
        pass

    #removes a quantity of symbol from portfolio.json
    def removeFromPortfolio(symbol, quantity, price):
        pass

    #buys quantity of symbol
    def buy(symbol, quantity, price):
        pass

    #sells quantity of symbol
    def sell(symbol, quantity, price):
        pass
        