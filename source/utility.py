import file_io as io

#adds orders to history
def addToHistory(PATH_TO_HISTORY_FILE, symbol, quantity, price):
    io.writeToTXTFile('../data/history.txt', data)

#adds a quantity of symbol to portfolio.json
def addToPortfolio(PATH_TO_PORTFOLIO_FILE, symbol, quantity, price):
    pass

#removes a quantity of symbol from portfolio.json
def removeFromPortfolio(PATH_TO_PORTFOLIO_FILE, symbol, quantity, price):
    pass

#buys quantity of symbol
def buy(PATH_TO_PORTFOLIO_FILE, symbol, quantity, price):
    pass

#sells quantity of symbol
def sell(PATH_TO_PORTFOLIO_FILE, symbol, quantity, price):
    pass