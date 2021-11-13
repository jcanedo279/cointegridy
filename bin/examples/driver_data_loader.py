from ..classes.Time import Time
from ..classes.data_loader import DataLoader, TreeLoader



def data_loader_driver():
    
    #################################
    ## PULL STATIC HISTORICAL DATA ##
    #################################
    
    VALID_INTERVALS = ['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M']
    
    interval_flag = '5m'
    
    db_start_date, db_end_date = (2021,1,28), (2021,2,1)
    db_start_Time, db_end_Time = Time.date_to_Time(*db_start_date), Time.date_to_Time(*db_end_date)
    
    ## UNCOMMENT TO UPDATE SHARPE RATIOS
    # pull_sharpe_ratios(start_Time=db_start_Time, end_Time=db_end_Time, interval_flag=interval_flag)
    
    ## UNCOMMENT TO 
    # num_symbols = 100
    # crypto_ids = get_best_stocks_from_CSV(SR_PATH, CSV_DEL, num_symbols)
    
    ## UNCOMMENT TO UPDATE HISTORICAL DATA
    # DataLoader.pull_data(start_Time=db_start_Time, end_Time=db_end_Time, interval_flag=interval_flag, bnc_ids=crypto_ids)
    
    # data_loader = DataLoader()
    
    ## GET AVAILABLE IDS FROM DRIVE
    # ids = data_loader.get_ids()
    # print(ids)

    
    
    ###################################
    ## PULL DYNAMMIC HISTORICAL DATA ##
    ###################################
    
    start_date, end_date = (2021,1,28), (2021,2,1)
    start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
    
    sample_symbol = 'BTCUSDT'
    
    tree_loader = TreeLoader()
    
    for datum in tree_loader[sample_symbol][start_Time:end_Time]:
        print(datum)


if __name__ == '__main__'():
    data_loader_driver()
    