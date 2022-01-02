class Error(Exception):
    # base class for other exceptions
    pass

class invalidLag(Error):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    
    def __str__(self) -> str:
        return "You have defined a lag besides seconds (s), minutes (m), or hours (h)."
    

class invalidTradeType(Error):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    
    def __str__(self) -> str:
        return 'you have tried to make a trade besides buy, sell, short or cover.'

class invalidDirection(Error):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    
    def __str__(self) -> str:
        return 'You tried to enter an event with a direction besides: \'over\', \'under\''

class invalidOrderID(Error):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    
    def __str__(self) -> str:
        return "Invalid order ID."

class invalidMethod(Error):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
    
    def __str__(self) -> str:
        return "The method you called is not among the list supported.\nPlease refer to basket.py for documentation."