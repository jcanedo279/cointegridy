# AVL tree implementation in Python

import sys



# Create a tree node
class TreeNode(object):
    def __init__(self, parent, key, node_type='root', linked_node=None):
        
        self.key, self.some_value = key, 10
        
        self.parent = parent
        self.node_type = node_type
        self.left, self.right = None, None
        
        self.height = 1
        
        ## A node that this node points to (like another child)
        self.linked_node = linked_node
        


class MultiWayAVLT(object):
    
    def __init__(self, iterable=[]):
        self.root = None
        for val in iterable:
            self.insert(val)
        
    def insert(self, key, linked_node=None):
        self.root, new_node = self._insert_node(self.root, key, linked_node=linked_node)
        self.root.node_type = 'root'
        return new_node

    # Function to insert a node
    def _insert_node(self, root, key, insert_type='root', linked_node=None):
        """
            Returns: new_root, inserted_node
        """
        inserted = None

        # Find the correct location and insert the node
        if not root:
            inserted = TreeNode(root, key, node_type=insert_type, linked_node=linked_node)
            return inserted, inserted
        elif key < root.key:
            root.left, inserted = self._insert_node(root.left, key, insert_type='left')
        else:
            root.right, inserted = self._insert_node(root.right, key, insert_type='right')

        root.height = 1 + max(self.getHeight(root.left),
                              self.getHeight(root.right))

        # Update the balance factor and balance the tree
        balanceFactor = self.getBalance(root)
        if balanceFactor > 1:
            if key < root.left.key:
                return self.rightRotate(root), inserted
            else:
                root.left = self.leftRotate(root.left)
                return self.rightRotate(root), inserted
        if balanceFactor < -1:
            if key > root.right.key:
                return self.leftRotate(root), inserted
            else:
                root.right = self.rightRotate(root.right)
                return self.leftRotate(root), inserted

        return root, inserted
    
    
    
    def delete(self, key):
        self.root = self._delete_node(self.root, key)
        self.root.node_type = 'root'
        

    # Function to delete a node
    def _delete_node(self, root, key):

        # Find the node to be deleted and remove it
        if not root:
            return root
        elif key < root.key:
            root.left = self._delete_node(root.left, key)
        elif key > root.key:
            root.right = self._delete_node(root.right, key)
        else:
            if root.left is None:
                temp = root.right
                if not temp: return None
                temp.parent, temp.node_type = root.parent if root else None, root.node_type
                root = None
                return temp
            elif root.right is None:
                temp = root.left
                if not temp: return None
                temp.parent, temp.node_type = root.parent if root else None, root.node_type
                root = None
                return temp
            temp = self.getMinValueNode(root.right)
            root.key = temp.key
            root.right = self._delete_node(root.right, temp.key)
        if root is None:
            return root

        # Update the balance factor of nodes
        root.height = 1 + max(self.getHeight(root.left),
                              self.getHeight(root.right))

        balanceFactor = self.getBalance(root)

        # Balance the tree
        if balanceFactor > 1:
            if self.getBalance(root.left) >= 0:
                return self.rightRotate(root)
            else:
                root.left = self.leftRotate(root.left)
                return self.rightRotate(root)
        if balanceFactor < -1:
            if self.getBalance(root.right) <= 0:
                return self.leftRotate(root)
            else:
                root.right = self.rightRotate(root.right)
                return self.leftRotate(root)
        return root


    # Function to perform left rotation
    """
      x                  y
     / \                / \ 
    a   y      ==>     x   g
       / \            / \ 
      b   g          a   b
    """
    def leftRotate(self, x):
        y = x.right
        b = y.left
        
        y.parent, y.node_type = x.parent if x else None, x.node_type
        
        ## x becomes y's left node
        y.left = x
        x.parent, x.node_type = y, 'left'
        
        ## b becomes x's right node
        x.right = b
        if b: b.parent, b.node_type = x, 'right'
        
        x.height = 1 + max(self.getHeight(x.left),
                           self.getHeight(x.right))
        y.height = 1 + max(self.getHeight(y.left),
                           self.getHeight(y.right))
        return y

    
    # Function to perform right rotation
    """
        x                  y
       / \                / \
      y   a      ==>     g   x
     / \                    / \
    g   b                  b   a
    """
    def rightRotate(self, x):
        y = x.left
        b = y.right
        
        y.parent, y.node_type = x.parent if x else None, x.node_type
        
        ## x becomes y's right node
        y.right = x
        x.parent, x.node_type = y, 'right'
        
        ## b becomes x's left node
        x.left = b
        if b: b.parent, b.node_type = x, 'left'
        
        x.height = 1 + max(self.getHeight(x.left),
                           self.getHeight(x.right))
        y.height = 1 + max(self.getHeight(y.left),
                           self.getHeight(y.right))
        return y


    # Get the height of the node
    def getHeight(self, root):
        if not root:
            return 0
        return root.height

    # Get balance factore of the node
    def getBalance(self, root):
        if not root:
            return 0
        return self.getHeight(root.left) - self.getHeight(root.right)

    def getMinValueNode(self, root):
        if root is None or root.left is None:
            return root
        return self.getMinValueNode(root.left)

    def preOrder(self, root):
        if not root:
            return
        print("{0} ".format(root.key), end="")
        self.preOrder(root.left)
        self.preOrder(root.right)
        
    def __repr__(self):
        self.printHelper(self.root, "", True)
        return ''

    # Print the tree
    def printHelper(self, currPtr, indent, last):
        if currPtr != None:
            sys.stdout.write(indent)
            if last:
                sys.stdout.write("R----")
                indent += "     "
            else:
                sys.stdout.write("L----")
                indent += "|    "
            print(currPtr.key)
            self.printHelper(currPtr.left, indent, False)
            self.printHelper(currPtr.right, indent, True)


if __name__=='__main__':
    
    nums = [33, 13, 52, 9, 21, 61, 8, 11]
    avlt = MultiWayAVLT(iterable=nums)

    print(avlt)

    avlt.delete(13)

    print(avlt)

    avlt.delete(52)

    print(avlt)

    avlt.delete(61)

    print(avlt)

