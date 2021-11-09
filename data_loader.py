import os
import csv
import pandas as pd
from bin.classes.time import Time
from bin.classes.processor import Processor

from datetime import datetime



TXT_DEL=' '
CSV_DEL=','

DATABASE_PATH = 'data/database.csv'
METADATA_PATH = 'data/metadata.txt'



def load_data():
    
    start_date, end_date = (2021,11,1), (2021,11,7)
    # start_Time, end_Time = Time.date_to_Time(*start_date), Time.date_to_Time(*end_date)
    
    pc_bnc = Processor('bnc')
    ids_bnc = pc_bnc.get_api_ids()[:5]
    
    
    """
        1 day ~ 289 5 minute intervals   -->   1 year ~ 105,485 lines
        
        20 lines ~ 8 kB   -->   105,485 lines ~ 42 MB
    """
    
    with open(METADATA_PATH, "w") as f_writer:
        f_writer.write(TXT_DEL.join(ids_bnc))
    
    
    if os.path.exists(DATABASE_PATH):
        with open(DATABASE_PATH, 'r') as f_reader:
            lines = f_reader.readlines()
            final_tmsp = float(lines[-1].split(CSV_DEL)[0])
            date = datetime.fromtimestamp(final_tmsp)
            start_date = (date.year,date.month,date.day)
    

    with open(DATABASE_PATH, 'w+', newline ='') as f_writer:
        writer = csv.writer(f_writer)
        
        for s_d,s_m,s_y in Time.iter_date(start_date, end_date, conv=True):
            print(f'PROCESSING   DAY {s_y,s_m,s_d} OF {end_date}\n\r', end='')
            # if os.path.exists(DATABASE_PATH): continue ## Continue if csv exists to avoid overlap
            cols = []
            for id in ids_bnc:
                id_response = pc_bnc.id_to_ohlc_seq(id, Time.date_to_Time(s_y,s_m,s_d), Time.date_to_Time(s_y,s_m,s_d+1), tmsp_interval="12h")[:-1]
                if not id_response:
                    cols.append([-1 for _ in range(len(cols[0]))])
                elif not cols:
                    tmsps, _open = zip(*[(int(d['open_tmsp']), d['open']) for d in id_response])
                    cols.append(tmsps)
                    cols.append(_open)
                else:
                    resp = [d['open'] for d in id_response]
                    cols.append(resp)
            for row_ind in range(len(cols[0])):
                writer.writerow([col[row_ind] for col in cols])



def get_data():
    """
        Returns: A DataFrame where the index are timestamps and the columns are the open prices of each id
    """
    df = pd.DataFrame()
    
    ids = None
    with open(METADATA_PATH, "r") as f_reader:
        ids = f_reader.read().split(TXT_DEL)
    
    if os.path.exists(DATABASE_PATH):
        with open(DATABASE_PATH, 'r') as f_reader:
            lines = csv.reader(f_reader)
            formed_line = next(lines, None)
            df = pd.DataFrame([[float(v) for v in formed_line[1:]]], columns=ids, index=[int(formed_line[0])])
            for line in lines:
                formed_line = line
                df = pd.concat([pd.DataFrame([[float(v) for v in formed_line[1:]]], columns=df.columns, index=[int(formed_line[0])]), df])
    
    return df
    




if __name__=='__main__':
    
    # load_data()
    
    df = get_data()
    print(df.head())
    
    pass
