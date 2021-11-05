from Time import Time
import time
from datetime import datetime, timezone


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
    

if __name__ == '__main__':
    
    main()
