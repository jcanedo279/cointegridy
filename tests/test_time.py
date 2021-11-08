from Time import Time
import time
from datetime import datetime, timezone


def test_1():
    loc_time = datetime.now().timestamp()
    utc_time = Time.arb_tmsp_to_utc_tmsp(loc_time, NAT_TZ)
    
    ref_utc_time = Time.utcnow()
    
    assert abs(ref_utc_time - utc_time) < 5

def test_driver():
    test_1()
    
def test_1():
    
    ### test that utc
    # print(time.time(), datetime.now(timezone.utc), datetime.utcnow())
    print(datetime.now(timezone.utc).timestamp(), datetime.utcnow().timestamp())
    pass

def test_2():
    
    
    pass




############
## Driver ##
############

def main():
    test_1()
    test_2()
    test_driver()

if __name__ == '__main__':
    
    main()
