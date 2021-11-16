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
        return f'{self.lower} {self.upper}'
    
    def __repr__(self):
        return self.repr()
        
        
class IntervalTree:
    
    def __init__(self):
        
        self.root = None
        
        
    def insert(self, lower, upper, value=None):
        """Insert based on key=lower

        Args:
            lower ([type]): [description]
            upper ([type]): [description]
            value ([type], optional): [description]. Defaults to None.
        """
        
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
        running_min, running_max = new_node.lower, new_node.upper
        parent_node = new_node.parent
        while parent_node:
            running_min, running_max = min(running_min, parent_node._min), max(running_max, parent_node._max)
            
            parent_node.height += 1
            parent_node._min, parent_node._max = running_min, running_max
            
            parent_node = parent_node.parent

        ## Rebalance the root
        if IntervalTree.balance_factor(self.root) > 1: ## Left heavy
            self.root = IntervalTree.r_rotate(self.root)
            self.root.height -= 1
        elif IntervalTree.balance_factor(self.root) < -1: ## Right heavy
            self.root = IntervalTree.l_rotate(self.root)
            self.root.height += 1
            
    
    
    def delete(self, lower, upper, value=None):
        
        if not self.root: return
        
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
        if (not target_node.left) and (not target_node.right):
            if not parent: ## No parent
                self.root = None
                return
            elif target_node.lower >= parent.lower: ## parent.right=target_node
                parent.right = None
            else: ## parent.left=target_node
                parent.left = None
            
        elif target_node.left and target_node.right:
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
        running_min, running_max = target_node._min, target_node._max
        if (target_node.lower < parent.left._min) and (target_node.lower < parent.right._min): ## If parent's min came from target_node
            running_min = min(target_node.left._min, target_node.right._min)
        if (target_node.upper > parent.left._max) and (target_node.upper < parent.right._max): ## If parent's min came from target_node
            running_max = max(target_node.left._max, target_node.right._max)
        cur_parent = parent
        while cur_parent:
            parent_node.height -= 1
            parent_node = parent_node.parent
        
        ## Rebalance the root
        if IntervalTree.balance_factor(self.root) > 1: ## Left heavy
            self.root = IntervalTree.r_rotate(self.root)
            self.root.height -= 1
        elif IntervalTree.balance_factor(self.root) < -1: ## Right heavy
            self.root = IntervalTree.l_rotate(self.root)
            self.root.height += 1
            
        

    
    
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
    
    print(itree)
    
    itree.insert(-2, -1, 'h')
    print(itree)
    
    print(itree.root._min, itree.root._max)
    
    # itree.delete(-2, -1, 'h')
    # print(itree)
    
    # itree.insert(-2, -1, 'h')
    # itree.delete(-1, 2, 'h')
    # print(itree)
    
    

if __name__ == '__main__':
    driver()
    
