import datetime
import pytz

"""
    A collection of utility functions that help handle time data
"""
    
def to_timezone(dtobj, trg_tz):
    trg_tzobj = trg_tz if type(trg_tz) is str else pytz.timezone(trg_tz)
    return dtobj.astimezone(trg_tzobj)


def from_tmsp(tmsp, trg_tz, short=False):
    trg_tzobj = trg_tz if type(trg_tz)!=str else pytz.timezone(trg_tz)
    if not type(tmsp) is int: tmsp = tmsp.timestamp()
    tmsp = tmsp/1000 if short else tmsp
    return datetime.datetime.fromtimestamp(tmsp, trg_tzobj)


def get_loc_time():
    return datetime.datetime.now()


def get_utc_time():
    return datetime.datetime.utcnow()
    
    