from cointegridy.src.classes.processor import Processor
from cointegridy.src.classes.Time import Time


def driver_processor():

    symbol = "DOGE"

    pc = Processor()
    t1, t2 = Time.date_to_Time(*(2021,10,29)), Time.date_to_Time(*(2021,11,1))

    for data in pc.symbol_to_ohlc_seq(symbol, t1, t2):
        pass
    
    symbol_to_denoms = pc.get_api_metadata()
    print(symbol_to_denoms)
    tickers = pc.get_api_tickers()
    

if __name__ == "__main__":
    driver_processor()
    
