from ..bin.classes.time import Time
from datetime import datetime, timezone

NAT_TZ = 'America/Los_Angeles'



def test_1():
    loc_time = datetime.now().timestamp()
    utc_time = Time.arb_tmsp_to_utc_tmsp(loc_time, NAT_TZ)
    
    ref_utc_time = Time.utcnow()
    
    print(utc_time, ref_utc_time)
    
def test_2():
    
    ### test that utc
    # print(time.time(), datetime.now(timezone.utc), datetime.utcnow())
    print(datetime.now(timezone.utc).timestamp(), datetime.utcnow().timestamp())
    pass




############
## Driver ##
############

def test_driver():
    test_1()
    test_2()

if __name__ == '__main__':
    
    test_driver()
