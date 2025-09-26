import math
from collections import namedtuple

BoxCoords = namedtuple('BoxCoords', 'left right top bottom')

class QSRRectangle:
    
    def __init__(self, coords, identifier=None):

        self.identifier = identifier
        if coords is None:
            self._left = 0
            self._right = 0
            self._top = 0
            self._bottom = 0
            print("No coords for identifer:", self.identifier, "Default to zero")
        else:
            self._left = coords.left
            self._right = coords.right
            self._top = coords.top
            self._bottom = coords.bottom
        self.bbox = BoxCoords(left=self.left, right=self.right, top=self.top, bottom=self.bottom)
        self.intervals = {'vertical' : {}, 'horizontal' : {}}

    def add_interval(self, orientation, interval_class):

        if orientation == 'horizontal':
            start_point = self._left
            end_point = self._right
        elif orientation == 'vertical':
            start_point = self._top
            end_point = self._bottom

        interval = interval_class(start_point=start_point, end_point=end_point, orientation=orientation)
        self.intervals[orientation][interval.method_identifier] = interval

    def get_interval(self, orientation, interval_class):

        if interval_class in self.intervals[orientation]:
            return self.intervals[orientation][interval_class]
        else:
            return None

    @property
    def box_coords(self):
        box_coords = ((self.left, self.top),   # top left corner
                      (self.right, self.top),   # top right corner
                      (self.left, self.bottom),   # bottom left corner
                      (self.right, self.bottom))   # bottomr right corner
        return box_coords
                      
    def set_bottom(self, value):

        self._bottom = value

    def set_left(self, value):

        self._left = value

    def set_right(self, value):

        self._right = value

    def set_top(self, value):

        self._top = value

    @property
    def left(self):
        return self._left
    
    @property
    def right(self):
        return self._right
    
    @property
    def top(self):
        return self._top
        
    @property
    def bottom(self):
        return self._bottom
    
    @property
    def height(self):
        return self.bottom-self.top

    @property
    def area(self):
        return max(0, self.length) * max(0, self.height)
        
    @property
    def length(self):
        return self.right-self.left
        
    @property
    def mid_vertical(self):
        return int((self.top+self.bottom)/2)

    @property
    def mid_horizontal(self):
        return int((self.left+self.right)/2)

    def union(self, other):
        union_rect = QSRRectangle(left=min(self.left, other.left), right=max(self.right, other.right), top=min(self.top, other.top), bottom=max(self.bottom, other.bottom))
        return union_rect
   
    def intersect(self, other):
        intersect_rect = QSRRectangle(BoxCoords(left=max(self.left, other.left), right=min(self.right, other.right), top=max(self.top, other.top), bottom=min(self.bottom, other.bottom)))
        return intersect_rect
   
    def split_at(self, x_split_point):

        left_side = QSRRectangle(BoxCoords(self.left, x_split_point, self.top, self.bottom))
        right_side = QSRRectangle(BoxCoords(x_split_point, self.right, self.top, self.bottom))

        return [left_side, right_side]

    def get_vertical_coords(self):
        return((self.top, self.bottom))
        
    def get_horizontal_coords(self):
        return((self.left, self.right))
        
    def is_above(self, other):
        if self.top < other.top:
            return True
        return False
    
    def is_below(self, other):
        if self.bottom < other.bottom:
            return True
        return False

    def is_leftof(self, other):
        if self.left < other.left:
            return True
        return False

    def is_rightof(self, other):
        if self.right > other.right:
            return True
        return False
    
    def is_equal(self,  other):
        if self.left != other.left:
            return False
        if self.right != other.right:
            return False
        if self.top != other.top:
            return False
        if self.bottom != other.bottom:
            return False
        return True
    
    def has_horizontal_overlap(self,  other):
        if self.left <= other.left <= self.right:
            return True
        if self.left <= other.right <= self.right:
            return True
        if other.left <= self.right and other.right >= self.right:
            return True
        return False
    
    def has_vertical_overlap(self, other):
        if self.top <= other.bottom <= self.bottom:
            return True
        if self.top <= other.top <= self.bottom:
            return True
        if other.top <= self.top and other.bottom >= self.bottom:
            return True
        return False
    
    def has_horizontal_abuttal(self, other):
        this_len = self.length
        other_len = other.length
        whole_len = self.union(other).length
        if whole_len == this_len + other_len:
            return True
        return False

    def has_vertical_abuttal(self, other):
        this_height = self.height
        other_height = other.height
        whole_height = self.union(other).height
        if whole_height == this_height + other_height:
            return True
        return False
    
    def has_overlap(self, other):
        if not self.has_horizontal_overlap(other):
            return False
        if not self.has_vertical_overlap(other):
            return False
        return True

    def is_disconnected(self, other):
        if not self.has_overlap(other):
            if not self.is_externally_connected(other):
                return True
        return False
    
    def is_externally_connected(self, other):
        if self.has_horizontal_abuttal(other):
            if self.has_vertical_abuttal(other) or self.has_vertical_overlap(other):
                return True
        if self.has_vertical_abuttal(other):
            if self.has_horizontal_abuttal(other) or self.has_horizontal_overlap(other):
                return True
        return False
    
    def is_proper_part(self, other):
        if not self.has_overlap(other):
            return False
        if self.is_above(other):
            return False
        if self.is_below(other):
            return False
        if self.is_leftof(other):
            return False
        if self.is_rightof(other):
            return False
        return True
    
    def is_tangential_proper_part(self, other):
        if self.is_equal(other):
            return False
        if not self.is_proper_part(other):
            return False

        return self.left == other.left or self.right == other.right or self.top == other.top or self.bottom == other.bottom
    
    def is_inverse_proper_part(self, other):
        return other.is_proper_part(self)
    
    def is_inverse_tangential_proper_part(self, other):
        return other.is_tangential_proper_part(self)
    
    def get_euclid(self, other):
        a_x = self.length / 2
        a_y = self.height / 2
        b_x = other.length / 2
        b_y = other.height / 2

        return ((a_x-b_x)**2 + (a_y-b_y)**2) ** 0.5

    def get_rcc8_class(self, other):
        if self.is_disconnected(other):
            return("DC")
        if self.is_externally_connected(other):
            return("EC")
        if self.is_equal(other):
            return("EQ")
        if self.is_proper_part(other):
            if self.is_tangential_proper_part(other):
                return("TPP")
            else:
                return("NTPP")
        if self.is_inverse_proper_part(other):
            if self.is_inverse_tangential_proper_part(other):
                return("TPPi")
            else:
                return("NTPPi")
        return("PO")
        
    def get_direction_of_other(self, other):
        # 0 = Connected
        # 1 = North
        # 2 = North East
        # 3 = East
        # 4 = South East
        # 5 = South
        # 6 = South West
        # 7 = West
        # 8 = North West
        if not self.is_disconnected(other):
            return(0)
        if self.has_vertical_overlap(other):
            vertical_orientation = 0 # Same
        elif self.is_below(other):
            vertical_orientation = -1 # Northern
        else:
            vertical_orientation = 1 # Southern
        if self.has_horizontal_overlap(other):
            horizontal_orientation = 0
        elif self.is_leftof(other):
            horizontal_orientation = -1
        else:
            horizontal_orientation = 1

        if horizontal_orientation == 0:
            return (1 + ((vertical_orientation > 0) * 4))
        else:
            return ((3 + (vertical_orientation*-horizontal_orientation)) + (horizontal_orientation > 0) * 4)

    def __str__(self):
        return ",".join(["L:",str(self.left), "R:",str(self.right), "T:",str(self.top), "B:",str(self.bottom)])
        
    def __repr__(self):
        
        return str(BoxCoords(self.left, self.right, self.top, self.bottom))

    def __eq__(self, other):

        return hash(self) == hash(other)

    def __hash__(self):

        return hash(((self.left, self.top), (self.right, self.bottom)))

    def _asdict(self):

        return BoxCoords(self.left, self.right, self.top, self.bottom)._asdict()

def coords_to_box(coordinates):

    left = min([k[0] for k in coordinates])
    right = max([k[0] for k in coordinates])
    top = min([k[1] for k in coordinates])
    bottom = max([k[1] for k in coordinates])
    return BoxCoords(left, right, top, bottom)

def parse_coords(coordinates, return_box=False):

    #return_box = False
    if isinstance(coordinates, BoxCoords):
        return coordinates

    if isinstance(coordinates, str):
        coord_parts = [[int(float(y)) for y in x.split(",")] for x in coordinates.split(" ")]
        # assume ordered left to right
        adjacent = coord_parts[-1][0]-coord_parts[0][0]
        opposite = coord_parts[-1][1]-coord_parts[0][1]
        #self.angle = math.degrees(math.atan(opposite/adjacent))
        coordinates = coord_parts

    if not return_box:
        return coordinates
    else:
        return coords_to_box(coordinates)

def isnumeric(x):

    try:
        float(x)
        return True
    except:
        return False

if __name__ == '__main__':
    
    # Test rectangles
    # Rectangle coordinates = [top left, top right, bottom right, bottom left]
    # Descriptions are relative to rect1

    rect1 = QSRRectangle(BoxCoords(10,50,10,20))
    print(rect1.split_at(30))
    exit()

    rect1 = QSRRectangle([(20,30),(60,30),(60,70),(20,70)])  # Box of interest - EQ
    other = QSRRectangle([(0,0),(100,0),(100,100),(0,100)])  # Large outer box - NTPP
    rect3 = QSRRectangle([(20,20),(80,20),(80,80),(20,80)])  # Medium outer box, touching side - TPP
    rect4 = QSRRectangle([(25,10),(45,10),(45,30),(25,30)])  # Small box abut to outside - EC
    rect5 = QSRRectangle([(30,40),(40,40),(40,45),(30,45)])  # Small inner box, no touching - NTPPi
    rect6 = QSRRectangle([(40,50),(50,50),(50,70),(40,70)])  # Small inner box, touching - TPPi
    rect7 = QSRRectangle([(50,50),(80,50),(80,60),(50,60)])  # Small box, overlapping - PO
    rect8 = QSRRectangle([(90,0),(100,0),(100,10),(90,10)])  # Small box outside - DC"
    
    A = rect5
    B = rect8
    print(A)
    print(B)
    print(A.union(B))
    #  EQ
    #  NTPP
    #  TPP
    #  EC
    #  NTPPi
    #  TPPi
    #  PO
    #  DC
    #print(rect1.get_rcc8_class(rect1))
    #print(rect1.get_rcc8_class(other))
    #print(rect1.get_rcc8_class(rect3))
    #print(rect1.get_rcc8_class(rect4))
    #print(rect1.get_rcc8_class(rect5))
    #print(rect1.get_rcc8_class(rect6))
    #print(rect1.get_rcc8_class(rect7))
    #print(rect1.get_rcc8_class(rect8))
    #print(rect1.get_direction_of_other(rect8)) # North east = 2
    #print(rect1.get_direction_of_other(other)) # Overlapping = 0"
