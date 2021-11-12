
from multiway_avlt import MultiWayAVLT
from intervalmap import intervalmap


class AVLIT:
    
    def __init__(self, iterable=[]):
        """
            Takes: An iterable of inclusive slice objects in the form ( ..., [start:stop:step], ... )
        """
        
        self.lower_tree, self.upper_tree = MultiWayAVLT(), MultiWayAVLT()
        
        self.lower_int_bounds, self.upper_int_bounds = [], []
        
        for slc in iterable:
            self.insert(slc)
        
    
    def insert(self, _slice):
        assert isinstance(_slice,slice)
        
        start, stop, step = _slice.start, _slice.stop, _slice.step 

        ub_node = self.upper_tree.insert(stop)
        self.lower_tree.insert(start, linked_node=ub_node)
        

    def __getitem__(self, _slice: slice) -> bool:
        assert isinstance(_slice,slice)
        
        print(_slice.start, _slice.stop)
        
        ## TODO: FINISH
        
        
    def get_start(self, start_key):
        possible_start = AVLIT.__get_start(start_key)
        if not possible_start: return None
        ## possible_start <= start_key
        
    
    @classmethod
    def __get_start(root, start_key):
        if not root: return None
        
        ## start_key < root --> search left for covered start
        if start_key < root.key:
            ## can't go left, start_key NOT COVERED
            if not root.left: return None
            ## can go left --> go left
            if start_key <= root.left: return AVLIT.__get_start(root.left, start_key)
        ## root <= start_key --> search right for closest cover <= root
        else:
            ## can't go right --> start_key not covered by right
            if not root.right: return root
            ## can go right --> try right
            return AVLIT.__get_start(root.right, start_key)
        
        
        
    
    
        
        
        
        
def loc_driver():
    avlit = AVLIT()
    
    avlit[2:3]


if __name__=='__main__':
    loc_driver()
