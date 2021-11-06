
import pytz
from datetime import datetime, timezone
import time

    
TIMEZONES = pytz.all_timezones_set
    
NAT_TZ = 'America/Los_Angeles'
NAT_TZOBJ = pytz.timezone(NAT_TZ)

UTC_TZOBJ = pytz.utc
    
class Time:
    
    """
        NOTE: Time is standardized in many ways:
        
        Reference:
            The time we use here is Possix time (measured as of 00:00:00 UTC on 1 January 1970)
        Timezone:
            Multiple times can be Possix reference times and be different times due to timezones, we
            standardize this by using UTC as the standard timeone
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
        
    def get_psx_tmsp(self):
        return self.utc_dtobj.timestamp()
    
    def to_tz(self, trg_tz=NAT_TZ):
        trg_tzobj = pytz.timezone(trg_tz) if type(trg_tz)==str else trg_tz
        
        try:
            return self.utc_dtobj.astimezone(trg_tzobj)
        except Exception as e:
            print(f'trg_tz={trg_tz} is not a valid target timezone, enter a valid string or a valid pytz timezone object')
    
    
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
    
    #######################
    ## CONVERT FROM DATE ##
    #######################
    
    @staticmethod
    def date_to_Time(year, month, day, hour=0, minute=0, second=0, microsecond=0):
        date = datetime(year, month, day, hour, minute, second, microsecond, tzinfo=timezone.utc)
        return Time(utc_tmsp=date.timestamp())
    
    
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
    






def test_1():
    loc_time = datetime.now().timestamp()
    utc_time = Time.arb_tmsp_to_utc_tmsp(loc_time, NAT_TZ)
    
    ref_utc_time = Time.utcnow()
    
    assert abs(ref_utc_time - utc_time) < 5



def test_driver():
    test_1()
    
    
if __name__ == '__main__':
    test_driver()


