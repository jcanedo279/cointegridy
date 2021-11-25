
from alg_pack.bin.classes.slicetree import SliceTree

def slicetree_driver():
    intervals = [
        (33,34,6,'a'),
        (13,14,3,'b'),
        (52,53,16,'c'),
        (9,10,1,'d'),
        (21,22,8,'e'),
        (61,62,2,'e'),
        (8,9,2,'fgh'),
        (11,12,4,'b'),
        (11,12,2,'jk'),
        (1,2,1,'kl'),
        (-10,-3,1,'kj'),
        (-7,-2,1,'yes'),
        (2,5,1,'target')
    ]


    myTree = SliceTree(intervals)

    print(myTree)


    # del myTree[33:34:6]
    # print(f"After Deleting: 33:34:6")
    # print(myTree)

    # # print(list(SliceTree.traverse(myTree.root)))


    # del myTree[21:22:8]
    # print(f"After Deleting: 21:22:8")
    # print(myTree)

    # del myTree[11:15:4]
    # print(f"After Deleting: 11:15:4")
    # print(myTree)


    # print(list(SliceTree.traverse(myTree.root)))


    # print('-'*10, 'QUERRY [2:12:1]', '-'*10)
    # for item in myTree[2:12:1]:
    #     print(item)
    # print('-'*30)
    
    
    for item in myTree.overlap_querry(slice(51,80,16)):
        # print(item)
        pass


    # for item in myTree.querry(slice(2,12,1)):
    #     print(item)


if __name__ == '__main__':
    slicetree_driver()


