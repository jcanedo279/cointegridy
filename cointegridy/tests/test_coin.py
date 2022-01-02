import shutil
import os
import numpy as np
import pandas as pd


from cointegridy.src.classes.coin import Coin
from cointegridy.src.classes.Time import Time

def test_init():
    '''Test only the implementation of coin, without basket'''
    C1 = Coin('sample')
    
    assert C1.name_ == 'sample'

def test_good():
    C1 = Coin('sample')

    data = pd.Series(list(range(100)))
    assert type(C1.is_good(data)) == type(bool())


