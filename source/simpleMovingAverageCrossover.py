import utility as util
import file_io as io

class simpleMovingAverageCrossover:
    def __init__(self, symbol):
        self.symbol= symbol

    def run(self):
        df = io.readFile('../analytics_output/output.csv')
        lines = df.readlines()
        for line in lines:
            data = line.split(',')