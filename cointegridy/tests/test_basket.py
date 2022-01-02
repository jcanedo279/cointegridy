import shutil
import os
import numpy as np
import pandas as pd


from cointegridy.src.classes.coin import Coin
from cointegridy.src.classes.basket import Basket
from cointegridy.src.classes.Time import Time

def test_init():
    '''
    Create a basket. By default this has no stored information
    '''

    coins = [Coin('ETH'),Coin('BTC'),Coin('LTC')]
    B1 = Basket(coins,coins[0])
    
    assert type(B1.coins_) == type(list())
    assert len(B1.coins_) == len(coins)
    assert B1.target_ != None



