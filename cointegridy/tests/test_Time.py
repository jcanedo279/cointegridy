from cointegridy.src.classes.Time import Time
from datetime import datetime, timezone

NAT_TZ = 'America/Los_Angeles'



def test_utcnow():
    loc_time = datetime.now().timestamp()
    utc_time = Time.arb_tmsp_to_utc_tmsp(loc_time, NAT_TZ)
    
    ref_utc_time = Time.utcnow()
    
    assert abs(utc_time-ref_utc_time) < 0.1

