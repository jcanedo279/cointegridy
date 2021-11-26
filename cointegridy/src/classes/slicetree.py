from collections import deque
from typing import Iterable

from treelib import Node, Tree

from cointegridy.src.classes.Time import Time


DEFAULT_STEP = 1



# Create a tree node
class Node(object):
    def __init__(self, start, stop, step=DEFAULT_STEP, value=None, parent=None):
        self.start,self.stop,self.step = start,stop,step
        self.value = value
        
        self.parent = parent
        self.left, self.right = None, None
        
        self._min,self._max,self._min_step,self._max_start = start,stop,step,start
        
        self.height = 1
    
    def __slice__(self):
        return (self.start, self.stop, self.step)
    
    def __hash__(self):
        return hash(self.__slice__())
    
    def __eq__(self, other):
        assert isinstance(other, Node)
        return True if (self.__slice__()==other.__slice__()) else False
    
    def __repr__(self):
        return self.repr()
    
    def repr(self):
        if (not isinstance(self.start,str)) and (not isinstance(self.stop,str)) and len(f'{int(self.start)}')>=10 and len(f'{int(self.stop)}')>=10:
            i_flag = self.step if not self.step in Time.valid_steps() else Time.valid_steps()[self.step]
            return f'{Time(utc_tmsp=self.start)}  ::  {Time(utc_tmsp=self.stop)}  ::  {i_flag}'
        
        return f'{self.start}:{self.stop}:{self.step} >> {self.value}'
    
    def patch(self):
        self._min,self._max,self._min_step,self._max_start,self.height = SliceTree.subtree_data(self)




class SliceTree(object):
    
    #######################
    ## SLICETREE BUILTIN ##
    #######################
    
    def __init__(self, iterable:Iterable=[], align_intervals=False, align_steps=False, default_step=DEFAULT_STEP):
        self.root = None
        self.interval_set = set()
        self.align_intervals, self.align_steps = align_intervals, align_steps
        self.default_step = default_step

        for _iter in iterable:
            if isinstance(_iter, tuple): self.insert_tup(_iter)
    
    def __setitem__(self, _slice:slice, value=None):
        interval = SliceTree.fix_interval(_slice, default_step=self.default_step)
        if interval in self.interval_set:
            return
        self.interval_set.add(interval)
        self.root = SliceTree.insert_node(_slice, self.root, None, value=value, default_step=self.default_step)
    
    def __delitem__(self, _slice:slice):
        interval = SliceTree.fix_interval(_slice, default_step=self.default_step)
        if interval not in self.interval_set:
            return
        self.interval_set.remove(interval)
        self.root = SliceTree.delete_node(_slice, self.root, None, default_step=self.default_step)
    
    def __getitem__(self, _slice:slice):

        querry_anc_generator = self.querry_anc(_slice)

        first_value = next(querry_anc_generator, None)
        if not first_value:
            return
        
        if first_value[0]:
            yield from self.traverse_inorder_interior(_slice, first_value[1])
        else:
            self.yield_wrapper(_slice, first_value[1], fix_start=False) ## Manually yield first_value as it may be outside start range

        for is_subtree, parent in querry_anc_generator:
            if is_subtree: yield from self.traverse_inorder_interior(_slice, parent)
            else: yield from self.yield_wrapper(_slice, parent)
    
    def __repr__(self):
        if not self.root:
            return 'EMPTY'
        
        print_tree = Tree()
        for node in SliceTree.traverse(self.root, method='PREORDER'):
            parent_repr = node.parent.repr() if node.parent else None
            print_tree.create_node(node.repr(), node.repr(), parent=parent_repr)
        print_tree.show()
        
        return '-'*20




    def overlap_querry(self, _slice:slice):

        start,stop,step=SliceTree.fix_interval(_slice, default_step=self.default_step)
        seq_max = start

        querry_generator = self.__getitem__(slice(start,stop,step))

        running_node = next(querry_generator, None)
        if not running_node or stop<=running_node.start: ## If no solution
            yield None, (start,stop,step)
            return
        if start < running_node.start:
            yield None, (start, running_node.start, step)
            seq_max = running_node.start
        
        
        for node in querry_generator:
            if seq_max >= stop: return
            if running_node.stop >= stop: break
            if node.start<=running_node.start: ## Update running node
                if node.stop > running_node.stop:
                    running_node = node
            else: ## New running node
                if node.stop > running_node.stop:
                    yield running_node.value, (seq_max, running_node.stop, running_node.step)
                    seq_max = running_node.stop
                    if seq_max < node.start: ## Gap
                        yield None, (seq_max, node.start, step)
                        seq_max = node.start
                    running_node = node
        if seq_max < running_node.stop and seq_max < stop:
            yield running_node.value, (seq_max, min(running_node.stop, stop), running_node.step)
            seq_max = min(running_node.stop, stop)
        if seq_max < stop:
            yield None, (seq_max, stop, step)




    

    ##### CORRECT INPUT INTERVAL #####
    @staticmethod
    def fix_interval(_slice:slice, default_step=DEFAULT_STEP):
        ## Fix interval
        assert isinstance(_slice,slice)
        start, stop, step = _slice.start, _slice.stop, _slice.step
        if not step: step = default_step
        if start>stop: ## FIX swap start and stop
            temp = start
            start, stop = stop, temp
        if (stop-start)%step != 0: ## FIX stop not divisible by step -> fix stop
            stop = start+(((stop-start)//step)+1)*step
        return (start,stop,step)


    ###################
    ## TREE UPDATING ##
    ###################

    def insert_tup(self, tup:tuple):
        if len(tup)==3:
            self.__setitem__(slice(tup[0],tup[1],tup[2]))
        elif len(tup)==4:
            self.__setitem__(slice(tup[0],tup[1],tup[2]), value=tup[3])

    @staticmethod
    def insert_node(_slice:slice, root:Node, parent:Node, value=None, default_step=DEFAULT_STEP):
        interval = SliceTree.fix_interval(_slice, default_step=default_step)
        start,stop,step = interval
        # Find the correct location and insert the node
        if not root:
            return Node(start, stop, step=step, value=value, parent=parent)
        elif start < root.start:
            root.left = SliceTree.insert_node(_slice, root.left, root, value=value, default_step=default_step)
        else:
            root.right = SliceTree.insert_node(_slice, root.right, root, value=value, default_step=default_step)

        root.patch()
        return SliceTree.rebalance(root)
    
    def successor(root):
        if root is None or root.left is None:
            return root
        return SliceTree.successor(root.left)

    @staticmethod
    def delete_node(_slice:slice, root:Node, parent:Node, default_step=DEFAULT_STEP):
        interval = SliceTree.fix_interval(_slice, default_step=default_step)
        start,stop,step = interval
        # Find the node to be deleted and remove it
        if not root: ## If no sol
            return root
        elif root.start==start and root.stop==stop and root.step==step: ## If we have found the sol
            if root.left is None:
                temp = root.right
                if temp: temp.parent = parent
                root = None
                return temp
            elif root.right is None:
                temp = root.left
                if temp: temp.parent = parent
                root = None
                return temp
            temp = SliceTree.successor(root.right)

            root.right = SliceTree.delete_node(slice(*temp.__slice__()), root.right, root, default_step=default_step)
            root.right.parent = root
            root.right.patch()
            root.right = SliceTree.rebalance(root.right)

            temp.left = root.left
            temp.left.parent = temp

            temp.right = root.right
            temp.right.parent = temp

            root = temp ## Replace root with temp
            if root: root.parent = parent
            
        elif start >= root.start: ## If sol to the right
            root.right = SliceTree.delete_node(_slice, root.right, root, default_step=default_step)
            if root.right:
                root.right.parent = root
        elif start <= root.start: ## If sol to the left
            root.left = SliceTree.delete_node(_slice, root.left, root, default_step=default_step)
            if root.left:
                root.left.parent = root
        if root is None:
            return root

        # Update the balance factor of nodes
        root.patch()
        return SliceTree.rebalance(root)
    

    ####################
    ## TREE QUERRYING ##
    ####################

    def querry_anc(self, _slice:slice):
        if not self.root: return
        
        lower_node = self.find_lower_node(_slice)
        upper_node = self.find_upper_node(_slice)

        if lower_node==upper_node:
            yield False, upper_node
            return
        
        """
            [If lower_node.stop < start --> gap between start and querry start
             If upper_node.stop < stop --> gap between querry stop and stop
             
             If any gaps, there can exist a node whose upper > start,stop; but searching requires O(n) time]
        """
        
        ## Determine all ancestors
        cur_anc, ancestry_set = upper_node, set()
        while cur_anc:
            ancestry_set.add(cur_anc)
            cur_anc = cur_anc.parent
        
        ## Determine lower ancestry set and root
        cur_anc, lower_anc_set = lower_node, set()
        while cur_anc:
            lower_anc_set.add(cur_anc)
            if cur_anc in ancestry_set:
                break
            cur_anc = cur_anc.parent
        root = cur_anc
        
        ## Determine upper ancestry set
        cur_anc, upper_anc_set = upper_node, set()
        while cur_anc:
            upper_anc_set.add(cur_anc)
            if cur_anc ==root:
                break
            cur_anc = cur_anc.parent
        
        ## This next part takes O(m) time where m is the number of intervals where start<=m.start<stop
        ## Yield over inorder interior of lower ancestry (not including root)
        cur_anc = lower_node
        while cur_anc != root:
            if not cur_anc.left and not cur_anc.right:
                yield False, cur_anc
            elif cur_anc.left and cur_anc.left in lower_anc_set: ## We came from left
                yield False, cur_anc
                if cur_anc.right: yield True, cur_anc.right
            elif cur_anc.right and cur_anc.right in lower_anc_set: ## We came from right
                if cur_anc.left: yield True, cur_anc.left
                yield False, cur_anc
            cur_anc = cur_anc.parent

        ## Yield over inorder interior of upper ancestry (including root, not including upper)
        while cur_anc != upper_node:
            if cur_anc.left and cur_anc.left in upper_anc_set: ## We are going left
                yield False, cur_anc
                if cur_anc.right: yield True, cur_anc.right
                cur_anc = cur_anc.left
            elif cur_anc.right and cur_anc.right in upper_anc_set: ## We are going right
                if cur_anc.left: yield True, cur_anc.left
                yield False, cur_anc
                cur_anc = cur_anc.right
            else:
                break
        
        ## Yield over inorder interior of upper subtree
        if upper_node.left: yield True, upper_node.left
        yield False, upper_node
    

    ################################
    ## MINIMALLY VIABLE SEARCHING ##
    ################################

    def yield_wrapper(self, _slice:slice, node:Node, fix_start=True):
        start,stop,step = SliceTree.fix_interval(_slice, default_step=self.default_step)
        if fix_start and start>node.start:
            yield
            return
        
        if node.start<stop and node.step<=step:
            if self.align_intervals and ((node.start-start)%step!=0):
                yield
                return
            if self.align_steps and ((step%node.step)!=0):
                yield
                return
            if step%node.step != 0: ## If the timesequence is not divisible
                yield
                return
            yield node
    
    def traverse_inorder_interior(self, _slice:slice, root:Node):
        if not root: return
        start,stop,step = SliceTree.fix_interval(_slice, default_step=self.default_step)
        if root.left and root.left._min<stop and root.left._max_start>=start and root.left._min_step<=step:
            yield from self.traverse_inorder_interior(_slice, root.left)
        yield from self.yield_wrapper(_slice, root)
        if root.right and root.right._min<stop and root.right._max_start>=start and root.right._min_step<=step:
            yield from self.traverse_inorder_interior(_slice, root.right)
        

    ############################
    ## QUERRY RANGE SEARCHING ##
    ############################
    
    def find_lower_node(self, _slice:slice):
        """
            [Given some querry _slice, we wish to find a node that overlaps _slice.start. If none exists, return the largest node smaller than _slice.start]
        """
        interval = SliceTree.fix_interval(_slice, default_step=self.default_step)
        start,stop,step = interval
        
        cur_node = self.root
        while cur_node:
            if (cur_node.start<=start<=cur_node.stop): break ## If we overlap start --> sol found
            elif cur_node.start < start: ## If we are to the left of stop --> go right
                if not cur_node.right or cur_node.right._min > stop: ## If we can't go right or going right skips start --> sol found
                    break
                cur_node = cur_node.right
            else: ## If we are to the right of stop --> go left
                if not cur_node.left: break
                cur_node = cur_node.left
        return SliceTree.find_densest_equivilancy(cur_node)
    
    def find_upper_node(self, _slice:slice):
        """
            [Given some querry _slice, we wish to find a node that overlaps _slice.stop. If none exists, return the largest node smaller than _slice.stop]
        """
        interval = SliceTree.fix_interval(_slice, default_step=self.default_step)
        start,stop,step = interval
        
        cur_node = self.root
        while cur_node:
            if (cur_node.start<=stop<=cur_node.stop): ## If we overlap stop --> sol found
                break
            if cur_node.start < stop: ## If we are to the left of stop --> go right
                if not cur_node.right or cur_node.right._min > stop: ## If we can't go right or going right skips stop --> sol found
                   break
                cur_node = cur_node.right
            else: ## If we are to the right of stop --> go left
                if not cur_node.left: break
                cur_node = cur_node.left
        return SliceTree.find_densest_equivilancy(cur_node)
    

    ###################################
    ## SUBTREE EQUIVALENCY SEARCHING ##
    ###################################

    @staticmethod
    def find_densest_equivilancy(cur_node:Node):
        """
            [Given some node, find the child of that node (with equivalent start,stop) with the smallest step.
             This is necessary because self-balancing implies that we don't know if equivalencies are to the left or right]
        """
        start,stop,step = cur_node.__slice__()
        
        frontier = deque([cur_node])
        min_step, min_node = step, cur_node
        while frontier:
            node = frontier.pop()
            if node.step < min_step:
                min_step, min_node = node.step, node
            if node.left and (node.left.start==start and node.right.stop==stop):
                frontier.appendleft(node.left)
            if node.right and (node.right.start==start and node.right.stop==stop):
                frontier.appendleft(node.right)
        return min_node
    
    ## TODO:: EXPERIMENTAL :: NOT SURE IF NECESSARY
    @staticmethod
    def find_first_equivilancy(_slice:slice, cur_node:Node):
        """
            [Given some cur_node with start,stop defined by _slice, returns the first node in cur_node's subtree
             with step defined by _slice]
        """
        start,stop,step = SliceTree.fix_interval(_slice)
        if cur_node.start!=start or cur_node.stop!=stop: return None
        if cur_node.step==step: return cur_node
        if cur_node.right:
            right = SliceTree.find_first_equivilancy(_slice, cur_node.right)
            if right: return right
        if cur_node.left:
            left = SliceTree.find_first_equivilancy(_slice, cur_node.left)
            if left: return left
        return cur_node


    ######################
    ## TREE REBALANCING ##
    ######################

    def get_height(root):
        if not root:
            return 0
        return root.height

    def get_balance(root):
        if not root:
            return 0
        return SliceTree.get_height(root.left) - SliceTree.get_height(root.right)

    @staticmethod
    def rebalance(root):
        balanceFactor = SliceTree.get_balance(root)

        # Balance the tree
        if balanceFactor > 1:
            if SliceTree.get_balance(root.left) >= 0:
                return SliceTree.r_rotate(root)
            else:
                root.left = SliceTree.l_rotate(root.left)
                return SliceTree.r_rotate(root)
        if balanceFactor < -1:
            if SliceTree.get_balance(root.right) <= 0:
                return SliceTree.l_rotate(root)
            else:
                root.right = SliceTree.r_rotate(root.right)
                return SliceTree.l_rotate(root)
        return root
    
    @staticmethod
    def l_rotate(x):
        """[Left rotate]
            x             y
             \           /
              y   -->   x
             /           \
            b             b
        """
        
        y = x.right
        y.parent = x.parent
        
        b = y.left
        y.left = x
        if y.left:
            y.left.parent = y
        
        x.right = b
        if x.right:
            x.right.parent = x
        
        x.patch()
        y.patch()

        return y

    @staticmethod
    def r_rotate(x):
        """[Right rotate]
              x          y
             /            \
            y      -->     x
             \            /
              b          b
        """
        
        y = x.left
        y.parent = x.parent
        
        b = y.right
        y.right = x
        if y.right:
            y.right.parent = y
        
        x.left = b
        if x.left:
            x.left.parent = x
        
        x.patch()
        y.patch()

        return y

    ## Get subtree data of node that is guaranteed to exist     Returns: (_min, _max, _min_step)
    def subtree_data(root):
        min_l, min_r = root.start if not root.left else root.left._min, root.start if not root.right else root.right._min
        max_l, max_r = root.stop if not root.left else root.left._max, root.stop if not root.right else root.right._max
        ms_l, ms_r = root.step if not root.left else root.left._min_step, root.step if not root.right else root.right._min_step
        maxs_l, maxs_r = root.start if not root.left else root.left._max_start, root.start if not root.right else root.right._max_start
        h_l, h_r = SliceTree.get_height(root.left), SliceTree.get_height(root.right)
        return (min(min_l,root.start,min_r), max(max_l,root.stop,max_r), min(ms_l,root.step,ms_r), max(maxs_l,root.start,maxs_r), 1+max(h_l,h_r))
    

    ###################
    ## DEBUG UTILITY ##
    ###################

    def traverse(root, method='INORDER'):
        if not root: return
        if method == 'PREORDER':
            yield root
            yield from SliceTree.traverse(root.left, method=method)
            yield from SliceTree.traverse(root.right, method=method)
        if method == 'INORDER':
            yield from SliceTree.traverse(root.left, method=method)
            yield root
            yield from SliceTree.traverse(root.right, method=method)
        if method == 'POSTORDER':
            yield from SliceTree.traverse(root.right, method=method)
            yield root
            yield from SliceTree.traverse(root.left, method=method)
    

