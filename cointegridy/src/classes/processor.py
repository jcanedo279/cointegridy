"""
Functions that get data from FTX.
"""
import os
from typing import Generator

import ccxt

from cointegridy.src.classes.Time import Time

from dotenv import load_dotenv
load_dotenv()


DEFAULT_NUM_STEPS = 500

class Processor:
    
    def __init__(self, exchange_id='binanceus'):
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_PRIVATE_KEY'),
            'timeout': 30*1000,
            'enableRateLimit': True,
        })
        self.exchange.load_markets()
    
    
    def symbol_to_ohlc_seq(self, symbol, start_Time, end_Time, denom='USD', interval_flag="6h") -> Generator:
        """
            exchange: exchange object, (e.g. ccxt.ftx())
            symbol: symbol for the product (e.g. BTC/USD)
            since (datetime.datetime): start of the data feed
            limit: number of data bars to get per request
            td_symbol: symbol for the timedelta, e.g. "1m" is 1 minute
            exchange_name: name to use in dataframe for exchange data; this can be anything\
        """
        
        assert interval_flag in Time.valid_flags()
        
        product = f'{symbol}/{denom}'
        
        start, stop, step = int(start_Time.get_psx_tmsp()*1000), int(end_Time.get_psx_tmsp()*1000), Time.parse_interval_flag(interval_flag)*1000
        limit = int((stop-start)//step)
        
        for datum in self.exchange.fetch_ohlcv(product, timeframe=interval_flag, since=start, limit=limit):
            yield [int(float(datum[0])/1000)] + [float(d) for d in datum[1:]]
            
    
    def get_api_tickers(self) -> list:
        return self.exchange.fetch_tickers().keys()
    
    
    def get_api_metadata(self) -> dict:
        symbol_to_denoms = {}
        for ticker in self.exchange.symbols:
            symbol,denom = ticker.split('/')
            if symbol in symbol_to_denoms:
                symbol_to_denoms[symbol].update(denom)
            else:
                symbol_to_denoms[symbol] = {denom}
        return symbol_to_denoms
