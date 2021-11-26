# Trader class
# A bot with a wallet that covers a basket and makes trades

import requests

from cointegridy.src.classes.basket import Basket
import cointegridy.src.classes.exceptions

class Trader():

    def __init__(self,basket,wallet):
        self.basket = basket
        self.wallet = wallet
        self.active_trades = set()
        self.past_trades = set()
    
    def enter_trade(symbol,amt,tradetype,stoploss,takeprofit):

        # Logic: include interface with wallet

        order_id = ''
        return order_id

    def exit_trade(order_id,amt):

        return None
    

