
import sys
import random as rd
import pandas as pd

from cointegridy.src.classes.Time import Time
from cointegridy.src.classes.data_loader import TreeLoader
import cointegridy.src.utils.stats as stats


class Sampler:
    
    def __init__(self):
        
        self.dataloader = TreeLoader()
        self.symbol_to_denoms = TreeLoader.pull_metadata()
    
    
    def symbol_baskets_gen(self, min_samp_size:int=4, max_samp_size:int=6, num_samps:int=100, sample_method='random'):
        """[Returns a generator of symbols baskets]

        Args:
            min_samp_size (int, optional): [Minimum size of a symbol basket]. Defaults to 4.
            max_samp_size (int, optional): [Maximum size of a symbol basket]. Defaults to 6.
            num_samps (int, optional): [Number of samples]. Defaults to 100.

        Yields:
            [Iterable]: [symbol basket iterable]
        """
        
        symbols = self.symbol_to_denoms.keys()
        
        if sample_method == 'random':
            for _ in range(num_samps):
                samp_size = rd.choice(range(min_samp_size, max_samp_size+1))
                yield rd.sample(symbols, samp_size)
        if sample_method == 'prop':
            num_cycles = num_samps//(max_samp_size-min_samp_size+1)
            for _ in range(num_cycles):
                for samp_size in range(min_samp_size, max_samp_size+1):
                    yield rd.sample(symbols, samp_size)
            for samp_size, samp_ind in range(min_samp_size, max_samp_size+1):
                if samp_ind >= max_samp_size - (num_cycles*(max_samp_size-min_samp_size+1)): break
                yield rd.sample(symbols, samp_size)


    def validate(self, symbol_baskets_gen, start_Time:Time, end_Time:Time, interval_flag='6h', validation_metric='open'):
        """[summary]
        
        Args:
            symbol_baskets_gen ([Iterable]): [Generator of symbol basket iterables]
            start_Time (Time): [Time object denoting starting valiaiton time]
            end_Time (Time): [Time object denoting ending valiaiton time]
            interval_flag (str, optional): [A string representation of the interval (ie '6h')]. Defaults to '6h'.
            validation_metric (str, optional): [The metric to use for validaiton (ie 'open')]. Defaults to 'open'.

        Yields:
            [Iterable]: [valid symbol basket iterable]
        """
        
        pass
        

