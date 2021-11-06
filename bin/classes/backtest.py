# Backtrader needs CSVs and is annoying.
# Writing my own
from datetime import timedelta
from basket import Basket
import exceptions

class Event():
    
    def __init__(self,target,direction,processor):
        self.processor = processor
        self.target = target
        self.isTrue = False

        if direction not in ['over','under']:
            raise exceptions.invalidDirection('You tried to enter an event with a direction besides :\'above\', \'below\'')
        
    def check(self,tmsp,prevstamp):
        # The .loc expressions for previous stamp need to be corrected so it can get the previous timestamp dynamically. I'm just dumb and don't know how to do that.

        if self.direction == 'over' and self.processor.portfolio.loc[prevstamp] < self.target and self.processor.portfolio.loc[tmsp] >= self.target: # THIS SHOULD BE THE PREVIOUS TIMESTAMP
                return True
        elif self.direction == 'under' and self.processor.portfolio.loc[prevstamp] > self.target and self.processor.portfolio.loc[tmsp] <= self.target: # THIS SHOULD BE THE PREVIOUS TIMESTAMP
                return True
        return False

class Strategy():

    def __init__(self,shortEntryPoint,longEntryPoint,shortExitPoint,longExitPoint,processor):

        self.shortEntryPoint = shortEntryPoint
        self.longEntryPoint = longEntryPoint
        self.shortExitPoint = shortExitPoint
        self.longExitPoint = longExitPoint

        self.longEntry = Event(longEntryPoint,'under',processor)
        self.shortEntry = Event(shortEntryPoint,'over',processor)
        self.longExit = Event(longExitPoint,'under',processor)
        self.shortExit = Event(shortExitPoint,'over',processor)

    def __str__(self):
        return(f'Strategy object \nEvents: ')

    def execute(self):
        if self.longEntry.check():
            return 'NL'
        elif self.shortEntry.check():
            return 'NS'
        elif self.longExit.check():
            return 'EL'
        elif self.shortExit.check():
            return 'ES'


class Trader():

    # Represents one agent trading on a basket

    def __init__(self,basket):

        # Object used to stream data
        self.funds = 0
        self.fees = {'maker':0,'taker':0}
        self.basket = basket
        self.positions = {x : 0 for x in self.basket.coins_}
        self.open_position = False
        self.dollars_per_trade = self.funds / 4

    def add_funds(self,cash):
        # Generally this will be something like 
        self.funds += cash
    
    def set_fees(self,maker,taker):
        # create your fee structure.
        # later this will become choose_broker

        self.fees['maker'] = maker
        self.fees['taker'] = taker
    
    def strat_init(self,bandAbove,bandBelow,mean):
        self.strategy = Strategy(bandAbove,bandBelow,mean,mean,self.basket.processor)
    
    def execute_strategy(self,tmsp):
        flag = self.strategy.execute()
        if flag[0] == 'N' and not self.open_position:
            if flag[1] == 'L':
                self.enter_spread_trade(tmsp,self.dollars_per_trade,'buy')
            else:
                self.enter_spread_trade(tmsp,self.dollars_per_trade,'short')
        elif flag[0] == 'E' and self.open_position:
            if flag[1] == 'L':
                self.spread_trade(tmsp,self.dollars_per_trade,'sell')
            else:
                self.spread_trade(tmsp,self.dollars_per_trade,'cover')

    def trade(self,tmsp,asset,amount,trade_type,lag='5s'):
        """
        For now, assume no fees. Eventually, I want to this to be
        either hard-coded or dynamically making broker API calls to incorporate
        fees and other payments. 

        General logic:
        
        For now, trades are executed at the next timestep. That means that 
        we need to set a timedelta
        """ 
        if trade_type in ['buy','cover']:
            amount = abs(amount)
        elif trade_type in ['sell','short']:
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
            
        # Execute trade at next timestep

        cost = self.basket.processor.data[asset.name_].loc[execution_time] * amount 
        
        # Calculate fees

        if trade_type in ['buy','cover']:
            self.funds -= (1 + self.fees['taker'])*cost
        else:
            self.funds -= (1 + self.fees['maker'])*cost

        self.positions[asset] += amount

    
    def spread_trade(self,tmsp,dollarAmt,trade_type):
        
        y = 0
        coeffs = self.basket.coef_
        for i,coin in enumerate(self.basket.coins_):
            y += self.processor.data[coin.name_]*coeffs[i]
        
        scale = dollarAmt / y

        for i,coin in enumerate(self.basket.coins_):

            self.trade(tmsp,coin,scale*coeffs[i],trade_type)


class Backtester():

    def __init__(self,start,end):
        self.start = start
        self.end = end

    def run(self):

        '''
        Execute backtesting over the time interval

        Create a trader
        Choose a strategy
        Add funds
        Set a date range and a broker

        Loop:
        at each timestep from start to stop:
        
            check exit events (by definition mutually exclusive)
            If one triggers, exit.

            If there is no open position:
                Check entry events
                if one is true, enter trade based on event 
        Otherwise: 
            Do nothing
        
        '''


        return None

        

