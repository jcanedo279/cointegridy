# Backtrader needs CSVs and is annoying.
# Writing my own
from datetime import timedelta

from cointegridy.src.classes.basket import Basket
from cointegridy.src.classes.exceptions import *
from cointegridy.src.classes.data_loader import TreeLoader,TreeSymbolLoader
from cointegridy.src.classes.Time import Time

from sys import argv

#############################
## Backtesting Environment ##
#############################

'''
Structure

A Trader object makes trades associated with a cointegrated Basket of coins. 

The trader has liquidity and makes trades based on the assumption that the linear combination of assets suggested by the cointegration test is a time series that will revert to the mean.

The trader keeps track of which trades to make using a Strategy object. This checks for four defined Events (objects): a long entry and exit, and a short entry and exit.

The trader only has one open position at a time but checks if it can/should make any trades at every timestep for now. 

TODOS

Figure out logic for opening and closing positions

Define a function to liquidate all positions
- for assessing P&L at end of run
- also this is important to have so we can have a manual stop-loss or simulate getting margin called

'''


class Event():
    
    def __init__(self,target,direction):

        '''
        An Event represents the price of an asset crossing a line with a direction.
        '''

        self.target = target

        if direction not in ['over','under']:
            raise invalidDirection()
        
    def check(self,tmsp,series):
        # The .loc expressions for previous stamp need to be corrected so it can get the previous timestamp dynamically. I'm just dumb and don't know how to do that.

        prevstamp = tmsp - timedelta(minutes = 5)

        # Note: this won't run properly until you add code to make these starts and stops into Time objects.
        
        if self.direction == 'over' and series[prevstamp] < self.target and series[tmsp] >= self.target:
                return True
        elif self.direction == 'under' and series[prevstamp] > self.target and series[tmsp] <= self.target:
                return True
        return False


class Strategy():

    '''
    The wrapper that defines when to buy and sell. For now, this is a simple mean reversion strategy. 
    
    Takes in a buy and sell point for short and long trades. 
    
    I eventually plan to make this more general.
    '''

    def __init__(self,shortEntryPoint,longEntryPoint,shortExitPoint,longExitPoint):

        self.shortEntryPoint = shortEntryPoint
        self.longEntryPoint = longEntryPoint
        self.shortExitPoint = shortExitPoint
        self.longExitPoint = longExitPoint

        self.longEntry = Event(longEntryPoint,'under')
        self.shortEntry = Event(shortEntryPoint,'over')
        self.longExit = Event(longExitPoint,'under')
        self.shortExit = Event(shortExitPoint,'over')

    def __str__(self):
        return(f'Strategy object \nEvents: ')

    def execute(self,tmsp,series):

        '''
        Check all events. They are mutually exclusive so we can check them in sequence.
        '''

        if self.longEntry.check(tmsp,series):
            return 'NL'
        elif self.shortEntry.check(tmsp,series):
            return 'NS'
        elif self.longExit.check(tmsp,series):
            return 'EL'
        elif self.shortExit.check(tmsp,series):
            return 'ES'


class Trader():

    '''
    A Trader represents one agent making decisions based on the spread associated with one basket of coins. 

    Traders have money, holdings, a latency to their exchange, and a broker with a fee structure. 

    
    '''
    def __init__(self,basket):

        # Object used to stream data
        self.funds = 0
        self.fees = {'maker':0,'taker':0,'short':0}
        self.basket = basket
        self.positions = {x : 0 for x in self.basket.coins_}
        self.open_position = False
        self.dollars_per_trade = self.funds / 4
        self.logfile = None
        self.series = self.basket.prices_['spread']


    def add_funds(self,cash):
        '''
        How much USDT, BNB etc do we want to put in the hands of our bot?
        ''' 
        self.funds += cash
    
    def set_dollars_per_trade(self,amt):
        self.dollars_per_trade = amt
    
    def set_logfile(self,fname):
        '''
        Create a file to log data
        '''
        self.outfile = fname

    def set_fees(self,maker,taker,short):
        '''
        Set up the fee structure associated with a broker

        Eventually we will create "brokers" to deal with this more explicitly
        '''

        self.fees['maker'] = maker
        self.fees['taker'] = taker
        self.fees['short'] = short
    
    def strat_init(self,bandAbove,bandBelow,mean,std):
        '''
        Choose a strategy to use. For now this will just be different types of mean reversion trades.
        '''

        self.strategy = Strategy(bandAbove,bandBelow,mean+std/2,mean-std/2)

    def trade(self,tmsp,asset,amount,trade_type,lag='5s'):
        """
        For now, assume no fees. Eventually, I want to this to be
        either hard-coded or dynamically making broker API calls to incorporate
        fees and other payments. 

        General logic:
        
        For now, trades are executed at the next timestep (lag accounts for slippage). That means that 
        we need to set a timedelta
        """ 

        if trade_type in ['buy','cover']:
            amount = abs(amount)
        elif trade_type in ['sell','short']:
            amount = abs(amount) * -1
        else:
            raise invalidTradeType()

        #count = int(''.join([x for x in lag if x.isnumeric()]))
        count = int(lag[:-1])
        unit = lag[-1]
        #unit = ''.join([x for x in lag if not x.isnumeric()])

        if unit == 's':
            delta = timedelta(seconds = count)
        elif unit == 'm':
            delta = timedelta(seconds = count*60)
        
        else:
            raise invalidLag()
        
        execution_time = tmsp + delta
            
        # Execute trade at next timestep

        cost = self.basket.prices[asset.name_][execution_time] * amount 
        
        # Calculate fees

        if trade_type in ['buy','cover']:
            total_cost = (1 + self.fees['taker'])*cost
            self.funds -=  total_cost
            self.log(tmsp,self.outfile,f'executed trade: {trade_type} {amount} {asset.name_} for total cost {total_cost}')
        else:
            total_cost = (1 + self.fees['maker'])*cost
            self.funds -= total_cost
            self.log(tmsp,self.outfile,f'executed trade: {trade_type} {amount} {asset.name_} for total cost {total_cost}')

        self.positions[asset] += amount

    
    def spread_trade(self,tmsp,dollarAmt,trade_type):

        if dollarAmt > self.funds:
            print('You tried to execute a trade with more money than you have. Done nothing.')
            return None
        '''
        Enter or exit a spread trading position at a time.

        dollarAmt represents the total amount we want to commit to this trade.

        Trade type is controlled by the flag trade_type, and it takes on values (str) of buy,sell,short and cover.
        '''

        y = 0
        coeffs = self.basket.coef_
        for i,coin in enumerate(self.basket.coins_):
            y += self.processor.data[coin.name_]*coeffs[i]
        
        scale = dollarAmt / y

        for i,coin in enumerate(self.basket.coins_):

            self.trade(tmsp,coin,scale*coeffs[i],trade_type)

    def execute_strategy(self,tmsp):
        '''
        Strat execute will return a flag. Based on this flag, the trader will make the associated trades if not already in a position.
        '''

        if not self.logfile:
            print('Don\'t run a trader without a logfile for now. Retry after calling trader.set_logfile.')
            return
        

        flag = self.strategy.execute(tmsp,self.series)
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
        
        self.log(tmsp,self.outfile)
    
    def log(self,tmsp,outfile,message=None):
        
        with open(outfile,'w+') as f:
            if message:
                f.write(str(tmsp) + ': ' + message)
            else:
                f.write(f'{tmsp}: Holdings{self.positions}\nLiquidity: {self.funds} USDT \n_____________\n')
    
    def __str__(self):
        return f'Trader object \nHoldings: {self.positions}\nLiquidity: {self.funds} USDT'


class Backtester():

    def __init__(self,start,end):
        self.start = start
        self.end = end

    def select_basket(self,basket):
        self.basket = basket
    
    def run(self,logfile):
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

        # Need some help figuring out exactly how to declare parameters of a backtesting run
        # For now I have placeholders

        placeholder = None
        trader = Trader(self.basket)
        trader.set_logfile(logfile+'.txt')

        trader.add_funds(200)
        trader.strat_init(placeholder,placeholder,placeholder)

        trader.set_fees(placeholder,placeholder)

        for time in self.basket.processor.get_data(self.start,self.end): 
            # I know this isn't an actual method but we gotta talk about end goals for the processor class
            trader.execute_strategy(time)

        return None


'''

'''
if __name__ == "__main__":
    
    log = argv[1]

    start_date, end_date = (2020,2,1), (2020,6,1)

    start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
    
    
    sample_symbol = 'ETH'
    sample_denom = 'USD'
    sample_interval = '6h'

    coinData = {(sample_symbol,sample_denom):
    [(start_date,end_date, sample_interval,'v1')]
    }

    #loader = TreeSymbolLoader(sample_symbol, sample_denom,mode='df')
    loader = TreeLoader(data=coinData,mode='df')

    #data = list(loader[start_Time:end_Time:Time.parse_interval_flag(sample_interval)])
    #print(data)
    data = loader[sample_symbol:sample_denom][start_Time:end_Time:Time.parse_interval_flag(sample_interval)]

    #bt = Backtester(start_Time,end_Time)
    
    #testBasket = Basket()
    #bt.run(logfile = log)
    #print([x for x in data])
    print(data)
    

