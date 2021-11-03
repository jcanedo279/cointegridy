
from collections import defaultdict
import heapq


class VirtMark:
    
    def __init__(self, init_investment=1000):
        
        self.id_to_denoms = defaultdict(lambda: (1))
        
        self.investment = init_investment
        
        self.assets = {
            
        }
        
    def get_denominations(self, id):
        return self.id_to_denoms[id]
    
    def buy(self, id, dollar):
        print(self.id_to_denoms[id])
        
    @staticmethod
    def coin_change(coins, amount):
        pass


def main():
    marty = VirtMark()
    
    marty.buy('id', 100)
    
    print(marty.coin_change([1, 3, 5], 11))


if __name__ == "__main__":
    main()
