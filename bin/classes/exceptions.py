class Error(Exception):
    # base class for other exceptions
    pass

class invalidLag(Error):
    pass

class invalidTradeType(Error):
    pass

class invalidDirection(Error):
    pass

class invalidOrderID(Error):
    pass

class notEnoughFunds(Error):
    pass