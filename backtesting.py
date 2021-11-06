# Backtrader needs CSVs and is annoying.
# Writing my own
from datetime import timedelta
from basket import Basket
import exceptions

#############################
## Backtesting Environment ##
#############################

'''
Structure

A Trader object makes trades associated with a cointegrated Basket of coins. 

The trader has liquidity and makes trades based on the assumption that the linear combination of assets suggested by the cointegration test is a time series that will revert to the mean.

The trader keeps track of which trades to make using a Strategy object. This checks for four defined Events (objects): a long entry and exit, and a short entry and exit.

The trader only has one open position at a time but checks if it can/should make any trades at every timestep for now. 


'''


#####################
## Todos for David ##
#####################

'''
Figre out logic for opening and closing positions

Define a function to liquidate all positions
- for assessing P&L at end of run
- also this is important to have so we can have a manual stop-loss or simulate getting margin called

'''


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

        '''
        Check all events. They are mutually exclusive so we can check them in sequence.
        '''

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
        '''
        How much USDT, BNB etc do we want to put in the hands of our bot?
        ''' 
        self.funds += cash
    
    def set_fees(self,maker,taker):
        '''
        Set up the fee structure associated with a broker

        Eventually we will create "brokers" to deal with this more explicitly
        '''

        self.fees['maker'] = maker
        self.fees['taker'] = taker
    
    def strat_init(self,bandAbove,bandBelow,mean):
        '''
        Choose a strategy to use. For now this will just be different types of mean reversion trades.
        '''

        self.strategy = Strategy(bandAbove,bandBelow,mean,mean,self.basket.processor)

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
    
    def __str__(self):
        return f'Trader object \nHoldings: {self.positions}\nLiquidity: {self.funds} USDT'


class Backtester():

    def __init__(self,start,end):
        self.start = start
        self.end = end

    def select_basket(self,basket):
        self.basket = basket
    
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

        # Need some help figuring out exactly how to declare parameters of a backtesting run
        # For now I have placeholders

        placeholder = None
        trader = Trader(self.basket)
        trader.add_funds(200)
        trader.strat_init(placeholder,placeholder,placeholder)

        trader.set_fees(placeholder,placeholder)

        for time in self.basket.processor.get_data(self.start,self.end): 
            # I know this isn't an actual method but we gotta talk about end goals for the processor class
            trader.execute_strategy(time)

        return None

        

