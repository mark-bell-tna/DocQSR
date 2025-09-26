from .QSRAllen import AllenIntervals

class SimpleAllenIntervals3(AllenIntervals):
    
    description_lookup = {'XY': {1: 'before', 2: 'overlaps', 3:'after'}, 'YX': {1: 'after', 2: 'overlaps', 3:'before'}}
                   
    def __init__(self, start_point, end_point, orientation):
        super().__init__(start_point, end_point, orientation)

    @staticmethod
    def get_description(value, direction='XY'):
        
        return SimpleAllenIntervals3.description_lookup[direction][value]
    
    def _calc_relationship(self, other):
        
        X = self
        Y = other
        if X.end_point < Y.start_point:
            return 1
        elif Y.end_point < X.start_point:
            return 3
        else:
            return 2
         
        return None  #self._calc_relationship(Y, X)   



if __name__ == '__main__':
    
    # Test rectangles
    # Rectangle coordinates = [top left, top right, bottom right, bottom left]
    # Descriptions are relative to rect1

    AI1 = SimpleAllenIntervals(10,20, 'H')
    
    for s in [3, 5, 7, 10, 25]:
        AI2 = SimpleAllenIntervals(s, s+5, 'H')
        #print(s, s+5)
        print("\t", AI1.get_relationship(AI2))
        #print("\t", AI1.get_relationship(AI2, True))

    
