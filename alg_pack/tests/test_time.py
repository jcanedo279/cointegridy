from alg_pack.bin.classes.Time import Time
from datetime import datetime, timezone

NAT_TZ = 'America/Los_Angeles'



def test_1():
    loc_time = datetime.now().timestamp()
    utc_time = Time.arb_tmsp_to_utc_tmsp(loc_time, NAT_TZ)
    
    ref_utc_time = Time.utcnow()
    
    assert abs(utc_time-ref_utc_time) < 0.01



############
## Driver ##
############

def test_driver():
    test_1()
    test_2()

if __name__ == '__main__':
    
    test_driver()
