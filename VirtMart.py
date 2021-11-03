
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
        m = [[0 for _ in range(amount + 1)] for _ in range(len(coins) + 1)]
        for i in range(amount + 1):
            m[0][i] = i

        for c in range(1, len(coins) + 1):
            for r in range(1, amount + 1):
                if coins[c - 1] == r:
                    m[c][r] = 1
                elif coins[c - 1] > r:
                    m[c][r] = m[c - 1][r]
                else:
                    m[c][r] = min(m[c - 1][r], 1 + m[c][r - coins[c - 1]])

        i = len(coins)
        j = amount
        ret = {k: 0 for k in coins}
        while j != 0:
            if m[i][j - coins[i - 1]] == m[i][j] - 1:
                ret[coins[i - 1]] += 1
                j = j - coins[i - 1]
            else:
                i = i - 1

        return ret


def main():
    marty = VirtMark()
    
    marty.buy('id', 100)
    
    print(marty.coin_change([1, 3, 5], 11))


if __name__ == "__main__":
    main()
