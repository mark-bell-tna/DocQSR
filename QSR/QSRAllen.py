class AllenIntervals:
    
    description_lookup = {'XY': {1: 'before', 2: 'equals', 3: 'meets', 4: 'overlaps', 5: 'during', 6: 'starts', 7: 'finishes', None : None},
            'YX': {1: 'after', 2: 'equals', 3: 'met by', 4: 'overlapped by', 5: 'contains', 6: 'started by', 7: 'finished by', None : None}}
                   
    matrix_lookup = {'finishes':1.4, 'during':1.5, 'starts':1.6,
                     'after':2.1, 'met by':2.2, 'overlapped by': 2.4, 'equals':2.5, 'overlaps':2.6, 'meets':2.8, 'before':2.9,
                     'started by':3.4, 'contains': 3.5, 'finished by': 3.6}
                   
    def __init__(self, start_point, end_point, orientation='horizontal'):
        self.start_point = min(start_point, end_point)
        self.end_point = max(start_point, end_point)
        self.mid_point = (self.end_point+self.start_point)/2
        self.orientation = orientation
        self.method_identifier = type(self).__name__

    #@staticmethod
    def get_matrix_pos(self, description):

         return self.matrix_lookup[description]
         
    #@staticmethod
    def get_description(self, value, direction='XY'):
        
        return self.description_lookup[direction][value]
    
    @property
    def length(self):
        return self.end_point-self.start_point
        
    @property
    def start(self):
        return self.start_point

    @property
    def end(self):
        return self.end_point

    def intersect(self, other):

        int_start = max(self.start, other.start)
        int_end = min(self.end, other.end)

        return AllenIntervals(max(0, int_start), max(0, int_end), orientation=self.orientation)

    def get_relationship(self, other):
        
        code = self.get_relationship_code(other)

        return self.get_description(code['value'], code['direction'])
     
    def get_relationship_code(self, other):
        
        if self.orientation != other.orientation:
            return None
        
        X = self
        Y = other
        
        relationship = self._relationship(other)
        
        return relationship

    def _relationship(self, other):
        
        relationship = self._calc_relationship(other)
        desc_key = 'XY'
        if relationship is None:
            relationship = other._calc_relationship(self)
            desc_key = 'YX'
        return {'value': relationship, 'direction': desc_key, 'extended': False, 'description': self.get_description(relationship, desc_key)}
        
    def _calc_relationship(self, other):
        
        X = self
        Y = other
        # 413 411 413 164
        if X.start_point < X.end_point < Y.start_point < Y.end_point:
            return 1
        if X.start_point == Y.start_point < X.end_point == Y.end_point:
            return 2
        if X.start_point < X.end_point == Y.start_point < Y.end_point:
            return 3
        if X.start_point < Y.start_point < X.end_point < Y.end_point:
            return 4
        if Y.start_point < X.start_point < X.end_point < Y.end_point:
            return 5
        if X.start_point == Y.start_point < X.end_point < Y.end_point:
            return 6
        if Y.start_point < X.start_point < X.end_point == Y.end_point:
            return 7
         
        return None  #self._calc_relationship(Y, X)   

    def __str__(self):
        
        return str({'start':self.start_point, 'mid':self.mid_point, 'end':self.end_point})

    def __repr__(self):

        return str(self)

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
    
    
