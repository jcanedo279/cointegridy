from collections import deque

from treelib import Node, Tree



class TreeNode:
    
    def __init__(self, lower, upper, value=None, parent=None):
        
        self.parent = parent
        self.left, self.right = None, None
        
        ## Key = lower
        self.lower, self.upper = lower, upper
        self.value = value
        
        ## Augmentations
        self.height = 1
        self._min, self._max = self.lower, self.upper
        
    def has_child(self):
        has_child = True if (self.left or self.right) else False
        return has_child
    
    def repr(self):
        return f'{self.lower} {self.upper} -> {self.height}'
    
    def __repr__(self):
        return self.repr()
        
        
class IntervalTree:
    
    def __init__(self):
        
        self.root = None
        self.intervals = set()
        
        
    def insert(self, lower:int, upper:int, value:TreeNode=None):
        """[Insert interval [lower,upper] based on lower]

        Args:
            lower (int): [lower bound]
            upper (int): [upper bound]
            value (TreeNode, optional): [some value]. Defaults to None.
        """
        
        ## Assert interval does not exist
        interval = (lower,upper,value)
        if interval in self.intervals:
            return -1
        self.intervals.add(interval)
        
        ## The node to be inserted
        new_node = TreeNode(lower, upper, value=value, parent=None)
        
        ## If no root, set root
        if not self.root:
            self.root = new_node
            return
        
        ## Insert node as target_node's child
        target_node = self.root
        while True:
            new_node.parent = target_node ## we are at target_node
            if lower < target_node.lower:
                if not target_node.left: ## We have found the node
                    target_node.left = new_node
                    break
                target_node = target_node.left
                
            if lower >= target_node.lower:
                if not target_node.right: ## We have found the node
                    target_node.right = new_node
                    break
                target_node = target_node.right
              
        ## Update parents
        if new_node.parent:
            cur_parent = new_node.parent
            while cur_parent:
                height_left = 0 if not cur_parent.left else cur_parent.left.height
                height_right = 0 if not cur_parent.right else cur_parent.right.height
                
                min_left = cur_parent.lower if not cur_parent.left else min(cur_parent.left._min, cur_parent.lower)
                max_left = cur_parent.upper if not cur_parent.left else max(cur_parent.left._max, cur_parent.upper)
                min_right = cur_parent.lower if not cur_parent.right else min(cur_parent.right._min, cur_parent.lower)
                max_right = cur_parent.upper if not cur_parent.right else max(cur_parent.right._max, cur_parent.upper)
                
                cur_parent.height = max(height_left, height_right) + 1
                cur_parent._min, cur_parent._max = min(min_left, min_right), max(max_left, max_right)
                
                cur_parent = cur_parent.parent

        ## Rebalance the root
        if IntervalTree.balance_factor(self.root) > 1: ## Left heavy
            self.root = IntervalTree.r_rotate(self.root)
        elif IntervalTree.balance_factor(self.root) < -1: ## Right heavy
            self.root = IntervalTree.l_rotate(self.root)
    
    
    def delete(self, lower:int, upper:int, value:TreeNode=None):
        """[Delete interval (lower,upper) based on lower]

        Args:
            lower (int): [lower bound]
            upper (int): [upper bound]
            value (TreeNode, optional): [some value]. Defaults to None.
        """
        
        ## Assert interval exists
        interval = (lower,upper,value)
        if interval not in self.intervals:
            return -1
        self.intervals.remove(interval)
        
        if not self.root: return
        
        ## Find target_node, the interval to be deleted
        target_node = self.root
        while True:
            if (lower==target_node.lower) and (upper==target_node.upper):
                break
            if lower < target_node.lower:
                if not target_node.left: return -1
                target_node = target_node.left
            if lower > target_node.lower:
                if not target_node.right: return -1
                target_node = target_node.right
        
        parent = target_node.parent
        if (not target_node.left) and (not target_node.right): ## No children
            if not parent: ## No parent
                self.root = None
            elif target_node.lower >= parent.lower: ## parent.right=target_node
                parent.right = None
            else: ## parent.left=target_node
                parent.left = None
            
        elif target_node.left and target_node.right: ## Both children
            succ = IntervalTree.successor(target_node)
            
            if not parent: ## No parent
                self.root = succ
                succ.parent = None
                
                succ.left = target_node.left
                succ.left.parent = succ
                
                succ.right = target_node.right
                succ.right.parent = succ
            
            elif target_node.lower >= parent.lower: ## parent.right=target_node
                parent.right = succ
                succ.parent = parent
                
                succ.left = target_node.left
                succ.right = target_node.right
                
                target_node.left.parent, target_node.right.parent = parent, parent
                
            else: ## parent.left=target_node
                parent.left = succ
                succ.parent = parent
                
                succ.left = target_node.left
                succ.right = target_node.right
            
                target_node.left.parent, target_node.right.parent = parent, parent
            
        elif target_node.left: ## Only left child
            if not parent: ## No parent
                self.root = target_node.left
            elif target_node.lower >= parent.lower: ## parent.right=target_node
                parent.right = target_node.left
                target_node.left.parent = parent
            else: ## parent.left=target_node
                parent.left = target_node.left
                target_node.left.parent = parent
           
        elif target_node.right: ## Only right child
            if not parent: ## No parent
                self.root = target_node.right
            elif target_node.lower >= parent.lower: ## parent.right=target_node
                parent.right = target_node.right
                target_node.right.parent = parent
            else: ## parent.left=target_node
                parent.left = target_node.right
                target_node.right.parent = parent
        
        ## Update height
        if parent:
            if target_node.lower >= parent.lower:
                parent.height += 1
            else:
                parent.height -= 1
                
        ## Update parents
        if parent:
            cur_parent = parent
            while cur_parent:
                height_left = 0 if not cur_parent.left else cur_parent.left.height
                height_right = 0 if not cur_parent.right else cur_parent.right.height
                
                min_left = cur_parent.lower if not cur_parent.left else min(cur_parent.left._min, cur_parent.lower)
                max_left = cur_parent.upper if not cur_parent.left else max(cur_parent.left._max, cur_parent.upper)
                min_right = cur_parent.lower if not cur_parent.right else min(cur_parent.right._min, cur_parent.lower)
                max_right = cur_parent.upper if not cur_parent.right else max(cur_parent.right._max, cur_parent.upper)
                
                cur_parent.height = max(height_left, height_right)+1
                cur_parent._min, cur_parent._max = min(min_left, min_right), max(max_left, max_right)
                
                cur_parent = cur_parent.parent
        
        ## Rebalance the root
        if IntervalTree.balance_factor(self.root) > 1: ## Left heavy
            self.root = IntervalTree.r_rotate(self.root)
        elif IntervalTree.balance_factor(self.root) < -1: ## Right heavy
            self.root = IntervalTree.l_rotate(self.root)
    
    
    def querry(self, querry:slice):
        
        if (self.root._max < querry.start) or (querry.stop < self.root._min): return []
        
        paths = []
        
        ## Get the starting upper bound of our interval chain
        start_node = self.rec_search_max_start(querry, self.root)
        start = querry.start
        if start_node:
            paths += [start_node]
            start = start_node.upper
        
        rec_paths,_ = self.rec_search(querry, self.root, start)
        paths += rec_paths
                
        return paths
    
    
    
    def rec_search(self, querry:slice, cur_node:TreeNode, path_max:int):
        """[Recursively search for spanning intervals that cover querry]

        Args:
            querry (slice): [a slice querry]
            cur_node (TreeNode): [the root of the search tree]
            path_max (int): [the running maximum we are trying to best]

        Returns:
            [([TreeNode],int)]: [a path of TreeNodes and the path maximum]
        """
        
        paths = []
        start, stop = querry.start, querry.stop
        lower, upper = cur_node.lower, cur_node.upper
        
        if path_max >= stop:
            return [], path_max
        
        ## Search left subtree
        if path_max<stop and cur_node.left and (cur_node.left._max>path_max):
            if cur_node.left.upper == cur_node.left._max: ## left is part of solution
                if cur_node.left.lower < stop:
                    paths += [cur_node.left]
                path_max = cur_node.left.upper
            else:
                left_path, path_max = self.rec_search(querry, cur_node.left, path_max)
                paths += left_path
          
        ## Search current
        if path_max<stop and lower<=path_max and upper>path_max: ## cur_node is part of solution
            paths += [cur_node]
            path_max = upper
        
        ## Search right subtree
        if path_max<stop and cur_node.right and (cur_node.right._max>path_max):
            if cur_node.right.upper == cur_node.right._max: ## right is part of solution
                if cur_node.right.lower < stop:
                    paths += [cur_node.right]
                path_max = cur_node.right.upper
            else:
                right_path, path_max = self.rec_search(querry, cur_node.right, path_max)
                paths += right_path
        
        return paths, path_max
    
    
    def rec_search_max_start(self, querry:slice, cur_node:TreeNode):
        """[summary]

        Args:
            querry (slice): [a slice querry]
            cur_node (TreeNode): [the root of the search tree]

        Returns:
            [TreeNode]: [the node with largest lower bound (<=querry.start) such that its upper bound is greater than querry.start]
                        (default None if no node exists)
        """
        
        start, stop = querry.start, querry.stop
        
        ## Search right subtree
        if cur_node.right and (cur_node.right._min<=start) and (cur_node.right._max>=start):
            if (cur_node.right.lower<=start) and (cur_node.right.upper>=start): ## right is part of solution
                return cur_node.right
            rec_left = self.rec_search_max_start(querry, cur_node.right)
            if rec_left: return rec_left
        
        ## Search current
        if (cur_node.lower<=start) and (cur_node.upper>=start):
            return cur_node
        
        ## Search left subtree
        if cur_node.left and (cur_node.left._min<=start) and (cur_node.left._max>=start):
            if (cur_node.left.lower<=start) and (cur_node.left.upper>=start):
                return cur_node.left
            rec_right = self.rec_search_max_start(querry, cur_node.left)
            if rec_right: return rec_right
    
        return None
        

    
    
    
    @staticmethod
    def successor(node):
        cur_node = node.right
        while cur_node:
            if (not cur_node.left) and (not cur_node.right): return cur_node
            if cur_node.left: cur_node = cur_node.left
            if cur_node.right: cur_node = cur_node.right
    
    
    @staticmethod  
    def balance_factor(node):
        if not node:
            return 0
        
        left_height = 0 if not node.left else node.left.height
        right_height = 0 if not node.right else node.right.height
        return left_height - right_height
    
    
    @staticmethod
    def r_rotate(x):
        """[Left subtree is heavy --> Right Rotation]
                x                  y
               / \                / \
              y    c    ===>     a   x
             / \                    / \
            a   b                  b   c
        """
        
        y, c = x.left, x.right
        a, b = y.left, y.right
        
        ## Left subtree is left heavy
        if IntervalTree.balance_factor(y) > 0:
            
            y.parent = x.parent
            
            y.right = x
            x.parent = y
            
            x.left = b
            if b:
                b.parent = x
            
        ## Left subtree if right heavy
        else:
            
            b.parent = x.parent
            
            b.left = y
            y.parent = b
            
            b.right = x
            x.parent = b
        
        ## Adjust heights
        h_b, h_c = 0 if not b else b.height, 0 if not c else c.height
        x.height = max(h_b, h_c)+1
        y.height = max(x.height, a.height)+1
        
        return y
    
    
    @staticmethod
    def l_rotate(x):
        """[Right subtree is heavy --> Left Rotation]
              x                     y
             / \                   / \
            a   y      ===>       x   c
               / \               / \
              b   c             a   b
        """
        
        a, y = x.left, x.right
        b, c = y.left, y.right
        
        ## Right subtree is left heavy
        if IntervalTree.balance_factor(y) > 0:
            
            b.parent = x.parent
            
            b.left = x
            x.parent = b
            
            b.right = y
            y.parent = b
        
        ## Right subtree is right heavy
        else:
            
            y.parent = x.parent
            
            y.left = x
            x.parent = y
            
            x.right = b
            if b:
                b.parent = x
        
        ## Adjust heights
        h_a, h_b = 0 if not a else a.height, 0 if not b else b.height
        x.height = max(h_a, h_b)+1
        y.height = max(x.height, c.height)+1
                
        return y
    
    
        
        
        
        
        
    def __repr__(self):
        
        if not self.root:
            print('EMPTY')
        
        print_tree = Tree()
        
        frontier = deque( [self.root] )
        while frontier:
            curr = frontier.pop()
            # print(curr, curr.parent)
            parent_repr = None if not curr.parent else curr.parent.repr()
            print_tree.create_node(curr.repr(), curr.repr(), parent=parent_repr)
            
            if curr.left:
                frontier.appendleft(curr.left)
            if curr.right:
                frontier.appendleft(curr.right)
        
        print_tree.show()
        
        return '-'*20
        
        
        
        
    
def driver():
    itree = IntervalTree()
    itree.insert(2, 4, 'hello')
    itree.insert(0, 4, 'its')
    itree.insert(3, 8, 'me again')
    itree.insert(-1, 2, 'h')
    itree.insert(-2, -1, 'h')
    print(itree)
    
    
    itree.delete(-2, -1, 'h')
    print(itree)
    
    itree.insert(-2, -1, 'h')
    # itree.delete(-1, 2, 'h')
    print(itree)
    
    querry = slice(-2,8)
    print(itree.querry(querry))
    
    

if __name__ == '__main__':
    driver()
    
