import analytics as A
import backtest as B

def main():
    print("script start...")
    #Analytics()
    Backtest()
    
def Analytics():
    a1 = A.Analytics()
    a1.run()
def Backtest():
    b1 = B.Backtest()
    b1.run()

if __name__ == '__main__':
    main()