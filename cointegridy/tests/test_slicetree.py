
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
    
    assert next(my_tree[1:1:0], None) == ('1_7_3', (1, 1, 0))
    assert next(my_tree[7:7:0], None) == ('1_7_3', (7, 7, 0))
    
    assert list(my_tree.full_querry(slice(1,1,0))) == [('1_7_3',(1,1,0))]
    assert list(my_tree.full_querry(slice(7,7,0))) == [('1_7_3',(7,7,0))]
    
    ## TEST 2 ##
    
    my_tree[7:9:3] = '7_10_3'
    
    assert next(my_tree[7], None)  == ('1_7_3', (7, 7, 0))
    assert next(my_tree[8], None) == ('7_10_3', (8, 8, 0))
    
    assert next(my_tree[12], None) == (None, (12,12,0))
    
    assert list(my_tree.full_querry(-1)) == [(None, (-1,-1,0))]
    assert list(my_tree.full_querry(3)) == [('1_7_3', (3,3,0))]
    

def test_edges():
    
    my_tree = SliceTree()
    my_tree[1:7:3], my_tree[7:9:3] = '1_7_3', '7_10_3'
    
    ## TODO:: Fix this
    # assert list(my_tree[-2:1:3]) == [SliceNode(1,7,step=3)]
    # assert list(my_tree[1:3:3]) == [SliceNode(1,7,step=3)]
    
    # assert list(my_tree[7:10:3]) == [SliceNode(1,7,step=3), SliceNode(7,10,step=3)]
    # assert list(my_tree[10:13:3]) == [SliceNode(7,10,step=3)]


def test_slicetree_overlap_depth():
    
    mounts = {
        (-2,24,2): 'v1',
        (38,45,1): 'v2',
        (38, 41,3): 'v3',
        (45,51,2): 'v4',
        (-1,2,1): 'v5',
        (-20,4,4): 'v6',
        (-50,-46,1): 'v7',
        (-47,-44,1): 'v8'
    }
    
    samp_querries = [
        (-2,24,2),
        (13,18,1),
        (2,30,2),
        (-51,-44,1),
        (-50,-48,1),
        (-45,-44,1),
        (-50,-44,1),
        (-40,-30,2),
    ]
    
    my_tree = SliceTree(data=mounts)
    
    for samp_start,samp_stop,samp_step in samp_querries:
        
        ## QUERRYING
        data = list( my_tree[samp_start:samp_stop:samp_step] )
        
        ## VERIFY QUERRY
        assert data[0][1][0] == samp_start
        
        for datum_ind in range(len(data)-1):
            datum, next_datum = data[datum_ind], data[datum_ind+1]
            assert datum[1][1] >= next_datum[1][0] ## Assert overlap
        
        assert data[-1][1][1] >= samp_stop
