from .QSRAllen import AllenIntervals

class AllenOverlapDegree(AllenIntervals):
    
    description_lookup = {'XY': {0 : 'none', 1: 'least', 2: 'mostly', 3:'total'}} # Not reversible, 'YX': {1: 'after', 2: 'overlaps', 3:'before'}}
                   
    def __init__(self, start_point, end_point, orientation):
        super().__init__(start_point, end_point, orientation)

    @staticmethod
    def get_description(value, direction='XY'):
        
        return AllenOverlapDegree.description_lookup[direction][value]
    
    def _calc_relationship(self, other):
        
        X = self
        Y = other

        x_len = X.end_point-X.start_point

        if X.start_point >= Y.end_point:
            return 0
        if X.end_point <= Y.start_point:
            return 0
        x_overlap = min(X.end_point, Y.end_point) - max(X.start_point, Y.start_point)

        if x_overlap == x_len:
            return 3
        if x_overlap >= x_len / 2:
            return 2
        return 1


if __name__ == '__main__':
    
    # Test rectangles
    # Rectangle coordinates = [top left, top right, bottom right, bottom left]
    # Descriptions are relative to rect1

    AI1 = AllenOverlapDegree(10,20, 'H')
    print(AI1.get_relationship(AllenOverlapDegree(10,20, 'H')))
    print(AI1.get_relationship(AllenOverlapDegree(17,20, 'H')))
    print(AI1.get_relationship(AllenOverlapDegree(15,20, 'H')))
    print(AI1.get_relationship(AllenOverlapDegree(12,20, 'H')))
    print(AI1.get_relationship(AllenOverlapDegree(20,20, 'H')))
    exit()
    
    for s in [3, 5, 7, 10, 25]:
        AI2 = AllenOverlapDegree(s, s+5, 'H')
        #print(s, s+5)
        print("\t", AI1.get_relationship(AI2))
        #print("\t", AI1.get_relationship(AI2, True))

    
