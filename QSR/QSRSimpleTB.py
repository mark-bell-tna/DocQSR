from .QSRAllen import AllenIntervals
from .QSRAllenTB import AllenIntervalsTB

class SimpleAllenIntervalsTB(AllenIntervalsTB):
    
    description_lookup = {'XY': {1: 'before', 2: 'equals', 3: 'before', 4: 'overlaps', 5: 'overlaps', 6: 'overlaps', 7: 'overlaps'},
                   'YX': {1: 'after', 2: 'equals', 3: 'after', 4: 'overlaps', 5: 'overlaps', 6: 'overlaps', 7: 'overlaps'}}
                   
    def __init__(self, start_point, end_point, orientation='horizontal', T=0):
        super().__init__(start_point, end_point, orientation)
        self.T = T
        
    def _calc_relationship(self, other):
        
        X = self
        Y = other
        if X.end_point < Y.start_point-self.T:
            return 1
        if (Y.start_point-self.T <= X.start_point <= Y.start_point+self.T) and \
           (Y.end_point-self.T <= X.end_point <= Y.end_point+self.T):
            return 2
        if Y.start_point-self.T <= X.end_point <= Y.start_point+self.T:
            return 3
        if (X.start_point < Y.start_point-self.T) and \
           (Y.start_point+self.T < X.end_point < Y.end_point-self.T):
            return 4
        if (X.start_point > Y.start_point+self.T) and \
           (X.end_point < Y.end_point-self.T):
            return 5
        if (Y.start_point-self.T <= X.start_point <= Y.start_point+self.T) and \
           (X.end_point < Y.end_point-self.T):
            return 6
        if (X.start_point > Y.start_point+self.T) and \
           (Y.end_point-self.T <= X.end_point <= Y.end_point+self.T):
            return 7
         
        return None  #self._calc_relationship(Y, X)   


if __name__ == '__main__':
    
    # Test rectangles
    # Rectangle coordinates = [top left, top right, bottom right, bottom left]
    # Descriptions are relative to rect1

    AI1 = AllenIntervals(10,20, 'H')
    
    for s in [3, 5, 7, 10, 12, 15, 18, 20, 25]:
        AI2 = AllenIntervals(s, s+5, 'H')
        #print(s, s+5)
        print("\t", AI1.get_relationship(AI2))
        #print("\t", AI1.get_relationship(AI2, True))
    
    for l in [[10,20], [10,25], [5,20], [8,22]]:
        AI2 = AllenIntervals(l[0],l[1],'H')
        print("\t", AI1.get_relationship(AI2))
    
    
