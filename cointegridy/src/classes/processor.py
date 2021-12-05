"""
Functions that get data from FTX.
"""
import os
from typing import Generator

import ccxt

from cointegridy.src.classes.Time import Time

from dotenv import load_dotenv
load_dotenv()


DEFAULT_NUM_STEPS = 499

class Processor:
    
    def __init__(self, exchange_id='binanceus'):
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_PRIVATE_KEY'),
            'timeout': 30*1000,
            'enableRateLimit': True,
        })
    
    def symbol_to_ohlc_seq(self, symbol, start_Time, end_Time, denom='USD', interval_flag="6h") -> Generator:
        """
            exchange: exchange object, (e.g. ccxt.ftx())
            symbol: symbol for the product (e.g. BTC/USD)
            since (datetime.datetime): start of the data feed
            limit: number of data bars to get per request
            td_symbol: symbol for the timedelta, e.g. "1m" is 1 minute
            exchange_name: name to use in dataframe for exchange data; this can be anything
            interval_flag: int + {"S", "m", "h" "D"}
        """
        
        assert interval_flag in Time.valid_flags()
        
        product = f'{symbol}/{denom}'
        
        start, stop, step = int(start_Time.get_psx_tmsp()*1000), int(end_Time.get_psx_tmsp()*1000), Time.parse_interval_flag(interval_flag)*1000
            
        limit = int((stop-start)/step)+1
        for datum in self.exchange.fetch_ohlcv(product, timeframe=interval_flag, since=int(start), limit=limit):
            yield [int(float(datum[0])/1000)] + datum[1:]
    
    
    def get_api_tickers(self) -> list:
        return self.exchange.fetch_tickers().keys()
    
    def get_api_symbols_to_denoms(self) -> dict:
        symbols_to_denoms = {}
        for ticker in self.get_api_tickers():
            symbol,denom = ticker.split('/')
            if symbol in symbols_to_denoms:
                symbols_to_denoms[symbol].update(denom)
            else:
                symbols_to_denoms[symbol] = {denom}
        return symbols_to_denoms
