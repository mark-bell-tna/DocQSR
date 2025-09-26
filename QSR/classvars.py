class X:

    i = 1

    def __init__(self):

        print(self.i)

class Y(X):

    i = 2

    def othermethod(self, z):
        pass
        
if __name__ == '__main__':

    x = X()
    y = Y()

    from QSR import AllenIntervals
    A = AllenIntervals(10,20,'h')
    print(A.get_matrix_pos('equals'))
