import pandas as pd
import datetime
from datetime import timezone
import pytz

start_date, end_date = (2018,9,1), (2020,9,1)

nat_tz = 'America/Los_Angeles'
nat_tzobj = pytz.timezone(nat_tz)
trg_tzobj = timezone.utc




def to_timezone(dtobj, trg_tz):
    trg_tzobj = trg_tz if type(trg_tz)!=str else pytz.timezone(trg_tz)
    return dtobj.astimezone(trg_tzobj)

def to_tmsp(utc_dtobj):
    return utc_dtobj.timstamp()

def from_tmsp(tmsp, trg_tz):
    trg_tzobj = trg_tz if type(trg_tz)!=str else pytz.timezone(trg_tz)
    return datetime.datetime.fromtimestamp(tmsp, trg_tzobj)
        
def get_loc_time():
    return datetime.datetime.now()
def get_utc_time():
    return datetime.datetime.utcnow()



test_dtobj = datetime.datetime(*start_date, tzinfo=trg_tzobj)






