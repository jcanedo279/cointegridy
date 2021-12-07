
from cointegridy.src.classes.Time import Time
from cointegridy.src.classes.data_loader import TreeLoader


def data_loader_driver():
    
    #################################
    ## PULL STATIC HISTORICAL DATA ##
    #################################
    
    db_start_date, db_end_date = (2021,1,28), (2021,4,1)
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
    
    sample_symbol, sample_denom = 'BTC', 'USD'

    data = {
        ('BTC','USD'): [
            ((2021,1,28), (2021,2,1), '6h', 'v1'),
            ((2020,12,16), (2020,12,23), '12h', 'v2'),
            ((2021,1,29), (2021,2,1), '4h', 'v3'),
            ((2020,11,19), (2020,11,22), '6h', 'v4'),
            ((2020,11,29),  (2020,12,1), '8h', 'v5'),
            ((2020,12,1), (2020,12,3), '4h', 'v6'),
        ]
    }

    tree_loader = TreeLoader()

    print(tree_loader[sample_symbol:sample_denom].slice_tree)




    
    ## QUERRYING
    querry_interval_flag = '6h'
    querry_sT, querry_eT = Time.date_to_Time(*(2021,1,1)), Time.date_to_Time(*(2021,1,5))
    

    data = list( tree_loader[sample_symbol:sample_denom][querry_sT:querry_eT:querry_interval_flag] )
    
    ## VERIFY QUERRY
    # data = list(data)
    print('QUERRYING: ', querry_sT.get_psx_tmsp(), querry_eT.get_psx_tmsp())
    # print(len(data))
    # for datum in data:
    #     print(datum)
    print('-'*20)
    
    for datum_ind in range(len(data)-1):
        datum, next_datum = data[datum_ind], data[datum_ind+1]
        if datum[0]+Time.parse_interval_flag(querry_interval_flag) != next_datum[0]:
            print(datum, next_datum)


if __name__ == '__main__':
    data_loader_driver()
    