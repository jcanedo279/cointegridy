from cointegridy.src.classes.cc_processor import Processor
from cointegridy.src.classes.Time import Time


def driver_cc_processor():

    symbol = "DOGE"

    pc = Processor()
    t1, t2 = Time.date_to_Time(*(2021,10,29)), Time.date_to_Time(*(2021,11,1))

    for data in pc.symbol_to_ohlc_seq(symbol, t1, t2):
        pass
    
    symbols = pc.get_api_symbols()
    print(symbols)
    tickers = pc.get_api_tickers()
    

if __name__ == "__main__":
    driver_cc_processor()
    
