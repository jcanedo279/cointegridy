# Backtrader needs CSVs and is annoying.
# Writing my own
from datetime import timedelta
from basket import Basket
import exceptions

class Event():
    
    def __init__(self,data,target,direction):
        self.data = data
        self.target = target
        self.isTrue = False

        self.direction == ''
        
    def check(self,tmsp):
        if self.price[tmsp] == self.target:
            self.isTrue = True
        return True

class Strategy():

    def __init__(self,name):
        self.name = name
        self.events = []

    def __str__(self):
        return(f'Strategy object\nName: {self.name}\nEvents: ')

class Backtester():

    def __init__(self):

        # Object used to stream data
        self.funds = 0
        self.positions = {}
        self.fees = {'maker':0,'taker':0}

    def add_funds(self,cash):
        # Generally this will be something like 
        self.funds += cash
    
    def set_fees(self,maker,taker):
        # create your fee structure.
        # later this will become choose_broker

        self.fees['maker'] = maker
        self.fees['taker'] = taker


    def trade(self,tmsp,asset,amount,b_or_s,lag='5s'):
        """
        For now, assume no fees. Eventually, I want to this to be
        either hard-coded or dynamically making broker API calls to incorporate
        fees and other payments. 

        General logic:
        
        For now, trades are executed at the next timestep. That means that 
        we need to set a timedelta
        """ 

        if b_or_s in ['buy','cover']:
            amount = abs(amount)
        elif b_or_s in ['sell','short']:
            amount = abs(amount) * -1
        else:
            raise exceptions.invalidTradeType('you have tried to make a trade besides buy, sell, short or cover.')


        #count = int(''.join([x for x in lag if x.isnumeric()]))
        count = int(lag[:-1])
        unit = lag[-1]
        #unit = ''.join([x for x in lag if not x.isnumeric()])

        if unit == 's':
            delta = timedelta(seconds = count)
        elif unit == 'm':
            delta = timedelta(seconds = count*60)
        
        else:
            raise exceptions.invalidLag("you have defined a lag besides seconds (s), minutes (m), or hours (h).")
        
        execution_time = tmsp + delta

        self.funds -= self.processor.data[asset].loc[execution_time] * amount 
        # Execute trade at next timestep, for now assume no fees

        if asset in self.positions.keys():
            self.positions[asset] += amount
        else:
            self.positions[asset] = amount
    
    def test(self,start,end,strategy):
        """
        Test outline:

        - Stream data for the outlined coins
        - At each timestep, the strategy uses a lookback window to make a decision
        - The strategy could theoretically execute multiple trades per timestep
        - 

        """
        

