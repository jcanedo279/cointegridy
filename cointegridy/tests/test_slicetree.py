
from cointegridy.src.classes.slicetree import SliceTree, SliceNode

# print('yikeß')

def test_null():
    
    empty_tree = SliceTree()
    
    assert list(empty_tree.querry_anc(slice(1,5,3))) == []
    assert list(empty_tree.full_querry(slice(1,5,3))) == [(None,(1,7,3))]

def test_point_querry():
    
    ## TEST 1 ##
    
    my_tree = SliceTree()
    my_tree[1:7:3] = '1_7_3'
    
    assert next(my_tree[1:1:0], None) == SliceNode(1,7,step=3)
    assert next(my_tree[7:7:0], None) == SliceNode(1,7,step=3)
    
    assert list(my_tree.full_querry(slice(1,1,0))) == [('1_7_3',(1,1,0))]
    assert list(my_tree.full_querry(slice(7,7,0))) == [('1_7_3',(7,7,0))]
    
    ## TEST 2 ##
    
    my_tree[7:9:3] = '7_10_3'
    
    assert next(my_tree[7], None)  == SliceNode(1,7,step=3)
    assert next(my_tree[8], None) == SliceNode(7,10,step=3)
    
    assert next(my_tree[12], None) == None
    
    assert list(my_tree.full_querry(-1)) == [(None, (-1,-1,0))]
    assert list(my_tree.full_querry(3)) == [('1_7_3', (3,3,0))]
    

def test_edges():
    
    my_tree = SliceTree()
    my_tree[1:7:3], my_tree[7:9:3] = '1_7_3', '7_10_3'
    
    assert list(my_tree[-2:1:3]) == [SliceNode(1,7,step=3)]
    assert list(my_tree[1:3:3]) == [SliceNode(1,7,step=3)]
    
    assert list(my_tree[7:10:3]) == [SliceNode(1,7,step=3), SliceNode(7,10,step=3)]
    assert list(my_tree[10:13:3]) == [SliceNode(7,10,step=3)]

