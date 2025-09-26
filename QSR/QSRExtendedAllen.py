from .QSRAllen import AllenIntervals

class ExtendedAllenIntervals(AllenIntervals):
    
    #description = {'XY': {1: 'before', 2: 'equals', 3: 'meets', 4: 'overlaps', 5: 'contains', 6: 'starts', 7: 'finishes'},
    #               'YX': {1: 'after', 2: 'equals', 3: 'met by', 4: 'overlapped by', 5: 'during', 6: 'started by', 7: 'finished by'}}
    
    extensions = set([4,5,6,7])
    extension_descriptions = {'XY': {4.1: 'mom', 4.2: 'mol', 4.3: 'lom', 4.4: 'lol', 5.1: 'ld', 5.2: 'cd', 5.3: 'rd', 6.1: 'ms', 6.2: 'ls', 7.1: 'mf', 7.2: 'lf'},
                              'YX': {4.1: 'momi', 4.2: 'moli', 4.3: 'lomi', 4.4: 'loli', 5.1: 'ldi', 5.2: 'cdi', 5.3: 'rdi', 6.1: 'msi', 6.2: 'lsi', 7.1: 'mfi', 7.2: 'lfi'}}
    direction_grid = [['lom','lf','rd','mf','cd','ms','ld','ls','mol'],
                      ['after','met by','loli','momi','equal','mom','lol','meets','before'],
                      ['lomi','lsi','ldi','msi','cdi','mfi','rdi','lfi','moli']]
    matrix_lookup = {}
    for i,row in enumerate(direction_grid):
        for j, item in enumerate(row):
            matrix_lookup[item] = (i+1) + (j+1)/10

    #for k,v in AllenIntervals.description_lookup['XY'].items():
    #    extension_descriptions['XY'][k] = v
    extension_descriptions['XY'].update(AllenIntervals.description_lookup['XY'])
    extension_descriptions['YX'].update(AllenIntervals.description_lookup['YX'])

    for k,v in AllenIntervals.description_lookup['YX'].items():
        extension_descriptions['YX'][k] = v


    def __init__(self, start_point, end_point, orientation):
        super().__init__(start_point, end_point, orientation)
        #self.start_point = min(start_point, end_point)
        #self.end_point = max(start_point, end_point)
        #self.orientation = orientation
        self.mid_point = (self.end_point+self.start_point)/2

    def get_relationship(self, other):
        
        code = self.get_relationship_code(other)

        if code['extended']:
            description = self.extension_descriptions[code['direction']][code['value']]
        else:
            description = self.description_lookup[code['direction']][code['value']]
        #print("\t",X.start_point, X.end_point, Y.start_point, Y.end_point)
        #return " ".join(['X', description, 'Y'])
        return description
        
     
    def get_relationship_code(self, other):
        
        if self.orientation != other.orientation:
            return None
        
        X = self
        Y = other
        
        #print(X.start_point, X.mid_point, X.end_point)
        #print(Y.start_point, Y.mid_point, Y.end_point)
        #print("\t", " " * X.start_point + "*" * (X.end_point-X.start_point), "(" + str(X.start_point) + "," + str(X.mid_point) + "," + str(X.end_point) + ")")
        #print("\t", " " * Y.start_point + "*" * (Y.end_point-Y.start_point), "(" + str(Y.start_point) + "," + str(Y.mid_point) + "," + str(Y.end_point) + ")")
        
        relationship = self._relationship(other)
        
        extension = self._extend(other, relationship['value'])
        if extension is None:
            return relationship
        return extension


    def _relationship(self, other):
        
        relationship = self._calc_relationship(other)
        desc_key = 'XY'
        if relationship is None:
            relationship = other._calc_relationship(self)
            desc_key = 'YX'
        return {'value': relationship, 'direction': desc_key, 'extended': False}
        
    def _extend(self, other, in_relationship, direction = 'XY'):
        
        extension = None
        if in_relationship not in self.extensions:
            return None
        relationship = in_relationship
        
        if relationship == 4:
            if self.start_point < other.start_point and self.end_point < other.end_point and self.mid_point >= other.start_point and self.end_point >= other.mid_point:
	            relationship += 0.1
            elif self.start_point < other.start_point and self.mid_point >= other.start_point and self.end_point < other.mid_point:
                relationship += 0.2
            elif self.mid_point < other.start_point and self.end_point >= other.mid_point and self.end_point < other.end_point:
                relationship += 0.3
            elif self.mid_point < other.start_point and self.end_point > other.start_point and self.end_point < other.mid_point:
	            relationship += 0.4
                
        if relationship == 5:
            if self.start_point > other.start_point and self.end_point <= other.mid_point:
                relationship += 0.1
            if self.start_point > other.start_point and self.start_point < other.mid_point and self.end_point > other.mid_point and self.end_point < other.end_point:
                relationship += 0.2
            if self.start_point >= other.mid_point and self.end_point < other.end_point:
                relationship += 0.3

        if relationship == 6:
            if self.end_point >= other.mid_point:
                relationship += 0.1
            if self.end_point > other.start_point and self.end_point < other.mid_point:
                relationship += 0.2
                
        if relationship == 7:
            if self.start_point > other.start_point and self.start_point <= other.mid_point:
                relationship += 0.1
            if self.start_point > other.mid_point and self.start_point < other.end_point:
                relationship += 0.2
        
        if in_relationship == relationship:
            return other._extend(self, relationship, 'YX')

        return {'value': relationship, 'direction': direction, 'extended': True}
        
    def __repr__(self):
        
        return str({'start':self.start_point, 'mid':self.mid_point, 'end':self.end_point})
        
    def __str__(self):
        
        return self.__repr__()

if __name__ == '__main__':
    
    # Test rectangles
    # Rectangle coordinates = [top left, top right, bottom right, bottom left]
    # Descriptions are relative to rect1

    AI1 = ExtendedAllenIntervals(10,13, 'H')
    
    for s in range(4,15,3):
        AI2 = ExtendedAllenIntervals(s, s+10, 'H')
        print("\t", AI1.get_relationship(AI2))

    #for l in [[10,20], [10,25], [5,20], [8,22]]:
    #    AI2 = ExtendedAllenIntervals(l[0],l[1],'H')
    #    print("\t", AI1.get_relationship(AI2))
    
    
    print(AI1.get_matrix_pos('mom'))
