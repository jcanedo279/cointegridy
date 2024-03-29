import copy
import pytz
from datetime import date, datetime, timezone, timedelta, tzinfo
import time
    
TIMEZONES = pytz.all_timezones_set
    
NAT_TZ = 'America/Los_Angeles'
NAT_TZOBJ = pytz.timezone(NAT_TZ)

UTC_TZOBJ = pytz.utc



###################
## PARSING FLAGS ##
###################

INT_TO_MULTIPLIER = {
    'm': 60,
    'h': 60*60,
    'd': 60*60*24,
    'w': 60*60*24*7,
    'M': 60*60*24*7*4
}

VALID_FLAGS = {'1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M'}

def parse_interval_flag(flag):
        last_char = 0
        for _char in flag:
            if _char.isnumeric(): last_char += 1
            
        return float(flag[:last_char]) * INT_TO_MULTIPLIER[flag[last_char:]]

VALID_STEPS = {parse_interval_flag(flag): flag for flag in VALID_FLAGS}

    
class Time:
    
    """
        NOTE: Time is standardized in many ways:
        
        Reference:
            The time we use here is Possix time (measured as of 00:00:00 UTC on 1 January 1970)
        Timezone:
            Multiple times can be Possix reference times and be different times due to timezones, we
            standardize this by using UTC as the standard timezone
        Scale:
            The standard LINUX timescale is seconds, but Binance uses ms so we need to convert
    """
    
    def __init__(self, utc_tmsp=None):

        ## if tmsp is numeric
        if type(utc_tmsp) in {int, float}:
            
            ## first make sure that tmsp is in the right unit (s)
            utc_tmsp_len = len(f'{int(utc_tmsp)}')
            if utc_tmsp_len >=12: # ms -> s
                utc_tmsp = utc_tmsp / 1000
        
        self.utc_dtobj = datetime.now(UTC_TZOBJ) if utc_tmsp==None else datetime.fromtimestamp(utc_tmsp)
        
    def __repr__(self):
        return f'{self.utc_dtobj.year}-{self.utc_dtobj.month}-{self.utc_dtobj.day}'
        # return f'{self.utc_dtobj.year}-{self.utc_dtobj.month}-{self.utc_dtobj.day}  {self.utc_dtobj.hour}:{self.utc_dtobj.minute}'
        
        
    def get_psx_tmsp(self):
        return self.utc_dtobj.timestamp()
    
    def to_tz(self, trg_tz=NAT_TZ):
        trg_tzobj = pytz.timezone(trg_tz) if type(trg_tz)==str else trg_tz
        
        try:
            return self.utc_dtobj.astimezone(trg_tzobj)
        except Exception as e:
            print(f'trg_tz={trg_tz} is not a valid target timezone, enter a valid string or a valid pytz timezone object')
    
    def add_seconds(self, seconds):
        days=0
        if seconds >= 60*60*24:
            days = seconds // 60*60*24
            seconds = seconds - days*60*60*24
            
        delta = timedelta(seconds=seconds, days=days) ## avoid seconds limit
        self.utc_dtobj += delta

        
    #############
    ## BUILTIN ##
    #############
    
    @staticmethod
    def sleep(secs=10): ## Wrap time sleep for easier imports
        time.sleep(secs)
    
    @staticmethod
    def timezones():
        return pytz.all_timezones_set
    
    @staticmethod
    def utcnow():
        return datetime.now(UTC_TZOBJ).timestamp()
    
    @staticmethod
    def get_epoch():
        """
            Returns: the native epoch, this should be 'Thu Jan  1 00:00:00 1970'
        """
        obj = time.gmtime(0)
        return time.asctime(obj)
    
    @staticmethod
    def add_seconds_from_Time(_Time, seconds):
        _T = copy.deepcopy(_Time)
        _T.add_seconds(seconds)
        return _T
    
    
    #########################
    ## INTERACT WITH FLAGS ##
    #########################
    
    @staticmethod
    def parse_interval_flag(flag):
        return parse_interval_flag(flag)
    
    @staticmethod
    def valid_flags():
        return VALID_FLAGS
    
    @staticmethod
    def valid_steps():
        return VALID_STEPS
    
    @staticmethod
    def int_to_multiplier():
        return INT_TO_MULTIPLIER
    
    
    #######################
    ## CONVERT FROM DATE ##
    #######################
    
    @staticmethod
    def date_to_Time(year, month, day, hour=0, minute=0, second=0, microsecond=0):
        date = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)
        return Time(utc_tmsp=date.timestamp())
    
    @staticmethod
    def datetime_to_Time(datetime):
        mock_Time = Time()
        mock_Time.utc_dtobj = datetime.astimezone(UTC_TZOBJ)
        return mock_Time
    
    #######################
    ## CONVERT FROM TMSP ##
    #######################
    
    @staticmethod
    def arb_tmsp_to_Time(tmsp, from_tz):
        return Time(utc_tmsp=Time.arb_tmsp_to_utc_tmsp(tmsp, from_tz))
        
    @staticmethod
    def arb_tmsp_to_utc_tmsp(tmsp, from_tz):
        if type(from_tz) is str: assert from_tz in TIMEZONES
        tzobj = pytz.timezone(from_tz) if type(from_tz) is str else from_tz
        return datetime.fromtimestamp(tmsp, tzobj).astimezone(UTC_TZOBJ).timestamp()
    
    
    ####################
    ## TIME ITERATORS ##
    ####################
    
    @staticmethod
    def iter_date(start_date, end_date, conv=False):
        """
            start_date, end_date in (YYYY,M,D) format
            conv: False -> string format return, True -> int tuple format return
            
            Returns: generator in (D,M,YYYY) format
        """
        
        def norm_date(d):
            return d if len(d)==2 else f'0{d}'
        
        s_y, s_m, s_d = [str(v) for v in start_date]
        e_y, e_m, e_d = [str(v) for v in end_date]
        
        s_m, s_d, e_m, e_d = norm_date(s_m), norm_date(s_d), norm_date(e_m), norm_date(e_d)
        
        start_date = date(int(s_y), int(s_m), int(s_d))
        end_date = date(int(e_y), int(e_m), int(e_d))
        delta = timedelta(days=1)
        
        while start_date <= end_date:
            s_d, s_m = f'{start_date.day}', f'{start_date.month}'
            if conv:
                yield (start_date.day, start_date.month, start_date.year)
            else:
                yield f'{norm_date(s_d)}-{norm_date(s_m)}-{start_date.year}'
            start_date += delta
    
    
    @staticmethod
    def iter_Time(start_Time, end_Time, sec_interval=600, conv=False):
        """
            start_Time, end_Time: random Time objects
            conv: False -> string format return, True -> Time format return
            
            Returns: Time object generator
        """
        
        def norm_date(d):
            return d if len(d)==2 else f'0{d}'
        
        delta = timedelta(seconds=sec_interval)
        
        cur_date, end_date = start_Time.utc_dtobj, end_Time.utc_dtobj
        
        
        while cur_date <= end_date:
            s_d, s_m = f'{cur_date.day}', f'{cur_date.month}'
            if conv:
                yield Time.datetime_to_Time(cur_date)
            else:
                yield f'{norm_date(s_d)}-{norm_date(s_m)}-{cur_date.year}'
            cur_date += delta
        
        
        
        
        pass




ZERO = timedelta(0)
class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO
        