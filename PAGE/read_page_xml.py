#!/usr/bin/python3

import xmltodict
from QSR import QSRRectangle, BoxCoords
from QSR.QSRRectangle import isnumeric, parse_coords, coords_to_box
#from QSRRectangles import Rectangle, BoxCoords, parse_coords, coords_to_box
import hashlib
import os
import lxml.etree
import copy
import math
from QSR import QSRAllenDegree
from collections import defaultdict
import numpy as np
from bisect import bisect_left
from pathlib import PosixPath, Path

sign = lambda x: math.copysign(1, x) if x != 0 else 0

def chartotype(text):
    outtext = []
    for t in text:
        c = ord(t)
        if 97 <= c <= 122:
            outtext.append("a")
        elif 65 <= c <= 90:
            outtext.append("A")
        elif 48 <= c <= 57:
            outtext.append("9")
        else:
            outtext.append(t)
    return "".join(outtext)

class LayoutStructure(object):

    v_overlap_comparator = lambda x, y : QSRAllenDegree.AllenOverlapDegree(x.top, x.bottom, 'V').get_relationship(QSRAllenDegree.AllenOverlapDegree(y.top, y.bottom, 'V'))
    h_overlap_comparator = lambda x, y : QSRAllenDegree.AllenOverlapDegree(x.left, x.right, 'H').get_relationship(QSRAllenDegree.AllenOverlapDegree(y.left, y.right, 'H'))

    @property
    def top(self):

        return self.coords.bbox.top

    @property
    def left(self):

        return self.coords.bbox.left

    @property
    def right(self):

        return self.coords.bbox.right

    @property
    def bottom(self):

        return self.coords.bbox.bottom

    @property
    def length(self):

        return self.right-self.left

    @property
    def height(self):

        return self.bottom-self.top

    @property
    def mid_vertical(self):

        return int((self.top+self.bottom)/2)

    @property
    def mid_horizontal(self):

        return int((self.right+self.left)/2)

    # gt, lt, and eq methods are aimed at ordering text lines and words by a left to right, top to bottom ordering
    def __gt__(self, other):

        if self.top >= other.bottom:
            return True
        if self.bottom <= other.top:
            return False

        if self.h_overlap_comparator(other) in ['mostly', 'equal', 'total'] or other.h_overlap_comparator(self) in ['mostly', 'equal', 'total']:
            # Occupying the same horizontal space
            return self.bottom > other.bottom

        if self.v_overlap_comparator(other) in ['mostly', 'equal', 'total'] or other.v_overlap_comparator(self) in ['mostly', 'equal', 'total']:
            if self.left < other.left:
                return False
            else:
                return True

        if self.bottom == other.bottom:
            return self.top > other.top
        return self.top > other.top

    def __eq__(self, other):

        if self.top == other.top and self.bottom == other.bottom and self.left == other.left and self.right == other.bottom:
            return True
        return False

    def __lt__(self, other):

        if self == other:
            return False
        if self > other:
            return False
        return True

class pageCoord:

    def __init__(self, coord_data):

        if isinstance(coord_data, QSRRectangle):
            self.bbox = coord_data
            self.raw = self.box_to_raw(self.bbox)
            self.parsed = parse_coords(self.raw)
            return
        elif isinstance(coord_data, str):
            self.raw = coord_data #['@points']
            if len(self.raw) == 0:
                self.parsed = []
                self.bbox = None
                return
            self.parsed = parse_coords(self.raw)
            self.bbox = QSRRectangle(coords_to_box(self.parsed))
            return
        elif isinstance(coord_data, pageCoord):
            self.bbox = coord_data.bbox
            self.parsed = coord_data.parsed
            self.raw = coord_data.raw
            return
        self.parsed = None
        self.bbox = None
        self.raw = None
        return

    @staticmethod
    def box_to_raw(box):

        return f"{box.left},{box.top} {box.left},{box.bottom} {box.right},{box.bottom} {box.right},{box.top}"

    @staticmethod
    def parsed_to_raw(parsed):

        return " ".join([",".join([str(x[0]), str(x[1])]) for x in parsed])

    @staticmethod
    def parsed_to_box(parsed):

        if parsed is None:
            return None

        left = min([x[0] for x in parsed])
        right = max([x[0] for x in parsed])
        top = min([x[1] for x in parsed])
        bottom = max([x[1] for x in parsed])

        return QSRRectangle(BoxCoords(left=left, right=right, top=top, bottom=bottom))

    @staticmethod
    def raw_to_box(raw):

        return pageCoord.parsed_to_box(pageCoord.raw_to_parsed(raw))

    @staticmethod
    def raw_to_parsed(raw):

        if len(raw) == 0:
            return None
        coord_parts = [[int(float(y)) for y in x.split(",") if isnumeric(y)] for x in raw.split(" ")]

    @staticmethod
    def split_horizontal(coords, x_pos):

        # Assumes that raw coordinates go in a loop anti-clockwise from bottom left
        left_side = [x for x in coords.parsed if x[0] < x_pos]
        if len(left_side) == 0:
            return {'left' : None, 'right' : coords.raw}
        if len(left_side) == len(coords.parsed):
            return {'left' : coords.raw, 'right' : None}

        split_coords = {'left' : [], 'right' : []}
        current_direction = 1
        for i in range(len(coords.parsed)-1):
            this_point = coords.parsed[i]
            next_point = coords.parsed[i+1]
            this_x, this_y = this_point
            next_x, next_y = next_point
            x_dist = next_x-this_x
            direction = sign(x_dist)
            if this_x < x_pos:
                split_coords['left'].append(this_point)
            if this_x > x_pos:
                split_coords['right'].append(this_point)
            if min(this_x, next_x) <= x_pos <= max(this_x, next_x):
                mean_y = int((this_y+next_y)/2)
                split_coords['left'].append([x_pos, mean_y])
                split_coords['right'].append([x_pos, mean_y])
        this_x, this_y = next_point
        if this_x < x_pos:
            split_coords['left'].append(next_point)
        if this_x > x_pos:
            split_coords['right'].append(next_point)


        return_val = {'left' : None, 'right' : None}
        if len(split_coords['left']) > 0:
            return_val['left'] = pageCoord.parsed_to_raw(split_coords['left'])
        if len(split_coords['right']) > 0:
            return_val['right'] = pageCoord.parsed_to_raw(split_coords['right'])
        #print("start:", coords.raw, "left:", pageCoord.parsed_to_raw(split_coords['left']))
        return return_val

class pageWord(LayoutStructure):

    def __init__(self, word_data):

        if isinstance(word_data, dict):
            self.id = word_data['id']
            #self.xpath = word_data['xpath']
            self.coords = pageCoord(word_data['Coords'])
            self.text = word_data['text']
            #if 'TextEquiv' in word_data and 'Unicode' in word_data['TextEquiv']:
            #    self.text = word_data['TextEquiv']['Unicode']
            #else:
            #    text = None
        else:
            self.id = None
            #self.xpath = None
            self.coords = None
            self.text = None
        self.baseline = None

    def __repr__(self):

        return self.text

    def __str__(self):

        return self.text

    def update_text(self, new_text):

        self.text = new_text

class pageLine(LayoutStructure):

    def __init__(self, line_data):

        self.id = line_data['id']
        #self.xpath = line_data['xpath']
        self.region_id = line_data['region_id']
        self.coords = pageCoord(line_data['Coords'])
        self.baseline = pageCoord(line_data['Baseline'])
        self.words = line_data['words']
        self.text = line_data['text']
        #if 'Word' in line_data:
        #    self.words = [pageWord(w) for w in line_data['Word']]

        #if points_type in line and isinstance(line[points_type], dict):
        #if 'TextEquiv' in line_data and 'Unicode' in line_data['TextEquiv']:
        #    self.text = line_data['TextEquiv']['Unicode']
        #else:
        #    text = None

    def get_coord_hash(self):

        return hashlib.md5((self.id, self.coords))

    def get_baseline_hash(self):

        return hashlib.md5((self.id, self.baseline))

    def __iter__(self):

        yield from self.words

    def __repr__(self):

        return str(self._asdict())

    def _asdict(self):

        return {'id' : self.id, 'text' : self.text, 'bbox' : self.coords.bbox}

    def get_word_at_index(self, at_index):

        return self.words[at_index]

    def update_word(self, new_text, at_index):

        self.words[position].update_text(new_text)

    def insert_word(self, word_text, bbox, word_id, at_index):

        new_word = pageWord({'id' : word_id, 'text' : word_text, 'coords' : bbox})
        self.words.insert(at_index, new_word)

    def delete_word(self, at_index):

        del self.words[at_index]

    def refresh_text(self):

        self.text = " ".join(self.words)

    def split_horizontal(self, x_pos):

        if len(self.words) == 0:
            if self.coords.bbox.right <= x_pos:
                return {'left' :  pageLine({'id' : self.id, 'region_id' : self.region_id, 'words' : self.words,  'Baseline' : self.baseline,  'Coords' : self.coords, 'text' : self.text}),
                        'right' : None}
            else:
                return {'left' : None,
                        'right' :  pageLine({'id' : self.id, 'region_id' : self.region_id, 'words' : self.words,  'Baseline' : self.baseline,  'Coords' : self.coords, 'text' : self.text})}

        left_word_list = []
        right_word_list = []

        word_list = {'left' : [], 'right' : []}

        return_val = {'left' : None, 'right' : None}

        for wd in self.words:
            if wd.right <= x_pos:
                word_list['left'].append(wd)
            elif wd.left >= x_pos:
                word_list['right'].append(wd)
            else:
                # how much overlap?
                if wd.mid_horizontal <= x_pos:
                    word_list['left'].append(wd)
                else:
                    word_list['right'].append(wd)

        cut_at = x_pos
        if len(word_list['left']) > 0:
            cut_at = max([w.right for w in word_list['left']])+1

        split_coords = self.coords.split_horizontal(self.coords, cut_at)
        split_baseline = self.baseline.split_horizontal(self.coords, cut_at)
        left_text = " ".join([wd.text for wd in word_list['left']])
        right_text = " ".join([wd.text for wd in word_list['right']])

        #print(self.id, "Before:", self.coords.bbox, self.text, "After left:", split_coords['left'], left_text, "After Right:", split_coords['right'], right_text)
        for side in ['left', 'right']:
            side_words = word_list[side]
            if len(side_words) > 0:
                return_val[side] = pageLine({'id' : self.id, 'region_id' : self.region_id, 'words' : side_words,
                                             'Baseline' : split_baseline[side], 'Coords' : split_coords[side], 'text' : " ".join([wd.text for wd in side_words])})

            #for wd in side_words:
            #    print(f"\t{side[0].upper()}:", wd.text, "L:", wd.left, "R:", wd.right, "M:", wd.mid_horizontal, "X:", x_pos, "C:", cut_at)

        return return_val


class pageRegion(LayoutStructure):

    def __init__(self, region_data, vertical_sort=True):

        self.id = region_data['id']
        #self.xpath = region_data['xpath']
        self.coords = pageCoord(region_data['Coords'])
        self.text_lines = region_data['lines']
        self.line_index = region_data['index']
        self._region_type = region_data['region_type']

        #if 'lines' in region_data:
        #    text_lines, self.line_index = self._read_lines(region_data['lines'])
        #    self.text_lines = [pageLine(l | {'region_id' : self.id}) for l in text_lines]

        '''
        if 'TextLine' in region_data:
            text_lines = region_data['TextLine']

            if isinstance(text_lines, dict):
                text_lines = [text_lines]

            self.text_lines = [pageLine(l | {'region_id' : self.id}) for l in text_lines]
            if vertical_sort:
                self.text_lines.sort(key=lambda x : x.coords.bbox.bottom)
            self.line_index = dict([(p.id, i) for i,p in enumerate(self.text_lines)])
        '''
        self.vertical_ordering = sorted(self.text_lines, key=lambda x : x.coords.bbox.bottom)


    def split_horizontal(self, x_pos):

        left_lines = []
        right_lines = []
        lines = {'left' : [], 'right' : []}
        return_val = {'left' : None, 'right' : None}

        for line in self:

            split_line = line.split_horizontal(x_pos)
            if split_line['left'] is not None:
                lines['left'].append(split_line['left'])
            if split_line['right'] is not None:
                lines['right'].append(split_line['right'])

        for side in ['left', 'right']:
            side_lines = lines[side]
            if len(side_lines) > 0:
                #for l in side_lines:
                    #if l.coords.bbox is None:
                    #    print(l, l.coords.raw, l.coords.parsed, l.coords.bbox, self.get_line_by_name(l.id))
                top = min([l.top for l in side_lines])
                left = min([l.left for l in side_lines])
                bottom = max([l.bottom for l in side_lines])
                right = max([l.right for l in side_lines])

                return_val[side] = pageRegion({'id' : self.id, 'lines' : lines[side],
                                               'Coords' : QSRRectangle(BoxCoords(top=top, bottom=bottom, left=left, right=right)), 'index' : self.line_index}) # last entry needs changing

        return return_val

    def get_line_by_bbox(self, bbox):

        split_above = bisect_left([x.bottom for x in self.vertical_ordering], bbox.top)
        if split_above >= len(self.vertical_ordering):
            print(bbox.top, split_above, len(self.vertical_ordering))
            return None
        this_line = self.vertical_ordering[split_above]
        best_overlap = 0
        best_line = None
        while this_line.top < bbox.bottom and split_above < len(self.vertical_ordering):
            this_line = self.vertical_ordering[split_above]
            max_top = max(this_line.top, bbox.top)
            min_bottom = min(this_line.bottom, bbox.bottom)
            if min_bottom-max_top > best_overlap:
                best_overlap = min_bottom-max_top
                best_line = this_line
            split_above += 1

        return best_line


    def get_line_by_name(self, line_name):

        if line_name in self.line_index:
            return self.text_lines[self.line_index[line_name]]
        return None

    @property
    def region_type(self):

        return self._region_type

    @property
    def line_count(self):

        return len(self.text_lines)

    def __repr__(self):

        return str({'id' : self.id, 'bbox' : self.coords.bbox, 'line_count' : len(self.text_lines)})

    def __str__(self):

        return self.__repr__()

    def __iter__(self):

        for line in sorted(self.text_lines):
            yield line

    @property
    def width(self):

        return self.coords.bbox.right-self.coords.bbox.left

    def get_region_baseline_hash(self):

        lines = [(ln.id, ln.baseline.raw) for ln in self]
        lines.sort(key=lambda x : x[0])
        this_hash = hashlib.md5()
        for ln in lines:
            this_hash.update(ln[1].encode('utf-8'))
        return this_hash

class pageXML(LayoutStructure):

    def __init__(self, xml_file, interval_list = None):

        self.xmlns = "{http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}"

        self.xml_original = None
        self.xml = None
        self.file_name = None
        self.regions = []
        self.regions_index = {}
        self.htr_model = None
        self.layout_model = None
        self.volume = None

        if xml_file is None:
            return

        if os.path.isfile(xml_file):
            self.file_name = xml_file
            self._gen_path_parts(xml_file)
            if os.path.getsize(xml_file) == 0:
                print("Empty file", xml_file)
                return
            self.xml = xmltodict.parse(open(xml_file, 'rb'))
            self.xml_original = lxml.etree.parse(open(xml_file,'rb'))
        else:
            # Could be the text of the XML rather then file itself
            self.xml = xmltodict.parse(xml_file)
            self.xml_original = lxml.etree.parse(xml_file)

        try:
            self.page = self.xml['PcGts']['Page']
            self.xml_root = self.xml_original.getroot()
        except:
            print("Not valid page xml")
            return

        self.metadata = None
        self.page = None
        for x in self.xml_root:
            if x.tag == f"{self.xmlns}Metadata":
                self.metadata = x
            if x.tag == f"{self.xmlns}Page":
                self.page = x
        if self.page is None:
            print("Not valid page xml")
            return

        self._image_height = int(self.page.attrib['imageHeight'])
        self._image_width = int(self.page.attrib['imageWidth'])
        self._image_file = self.page.attrib['imageFilename']
        self.regions, self.regions_index = self._read_regions()

    def _gen_path_parts(self, xml_file):

        if isinstance(xml_file, PosixPath):
            self.layout = xml_file.parents[0].split("-")[1]
            self.htr = xml_file.parents[1].split("-")[1]
            self.volume = xml_file.parents[2]
        else:
            path_parts = xml_file.split("/")
            self.layout = path_parts[-2].split("-")[1]
            self.htr = path_parts[-3].split("-")[1]
            self.volume = path_parts[4]

    def get_path_parts(self):

        return self.volume, self.htr, self.layout

    def save_to_file(self, xml_file_name, overwrite=False):

        if os.path.isfile(xml_file_name) and not overwrite:
            print("File exists, set overwrite=True to save")
            return

        et = lxml.etree.ElementTree(self.xml.root)
        et.write(xml_file_name, pretty_print=True)

    def _split_coords(self, coords, x_pos):

        left_side = [x for x in coords if x[0] < x_pos]
        left_change = [sign(x[0]-left_side[i-1][0] if i > 0 else x[0]) for i, x in enumerate(left_side)]
        left_turn = next(i for i,x in enumerate(left_change) if x < 1)
        if left_side[left_turn-1][0] < x_pos:
            left_side.insert(left_turn, [x_pos-1, left_side[left_turn-1][1]])
            left_turn += 1
        if left_side[left_turn][0] < x_pos:
            left_side.insert(left_turn, [x_pos-1, left_side[left_turn][1]])
            left_turn += 1

        right_side = [x for x in coords if x[0] >= x_pos]
        right_change = [sign(x[0]-right_side[i-1][0] if i > 0 else x[0]) for i, x in enumerate(right_side)]
        right_turn = next(i for i,x in enumerate(right_change) if x < 1)
        if right_side[0][0] != x_pos:
            right_side.insert(0, [x_pos, right_side[0][1]])
            right_turn += 1
        if right_side[-1][0] != x_pos:
            right_side.append([x_pos, right_side[-1][1]])

        return (left_side, right_side)

    def split_region_vertically(self, region_id, y_pos):

        region = self.get_region_by_name(region_id)
        #xml_region = self.xml_root.xpath(reg.xpath)[0]
        #print(xml_region)
        #parent = xml_region.getparent()
        #new_region = lxml.etree.SubElement(parent, xml_region.tag, xml_region.attrib)
        new_region_id = len(self.regions)+1
        for i in range(len(self.regions)):
            if self.regions[i].id == f"tr_{new_region_id}":
                new_region_id += 1
        new_region_id = f"tr_{new_region_id}"

        new_lines = []
        new_index = {}

        for i, line in enumerate(region):
            if line.coords.bbox.top > y_pos:
                new_index[line.id] = len(new_index)
                del region.line_index[line.id]
        new_lines = [l for l in region.text_lines if l.id in new_index]
        old_lines = [l for l in region.text_lines if l.id in region.line_index]
        old_index = [(l, i) for i,l in enumerate(old_lines)]
        region.text_lines = old_lines
        region.line_index = old_index
        new_bbox = BoxCoords(top=y_pos+1, bottom=region.coords.bbox.bottom, left=region.coords.bbox.left, right=region.coords.bbox.right)
        old_bbox = BoxCoords(top=region.coords.bbox.top, bottom=y_pos, left=region.coords.bbox.left, right=region.coords.bbox.right)
        region.coords = pageCoord(QSRRectangle(old_bbox))

        new_region = pageRegion({'id' : new_region_id, 'xpath' : None, 'Coords' : QSRRectangle(new_bbox), 'lines' : new_lines, 'index' : new_index})
        self.regions.append(new_region)

    def split_region_horizontal(self, region_id, x_pos):

        region = self.get_region_by_name(region_id)
        split = region.split_horizontal(x_pos)
        old_idx = self.regions_index[region_id]
        if split['left'] is not None and split['right'] is not None:
            self.regions[old_idx] = split['left']
            self.regions.append(split['right'])
            self.regions_index[self.regions[-1].id] = len(self.regions_index)

    def split_region_horizontally(self, region_id, x_pos):

        # Needs a parameter for direction - are we splitting left or right? Or is it always to the right, even if majority of lines are right of x_pos?
        # Not a precise split. Identify words which fall either side.
        # Separate function will resize region dimensions according to contents later
        # First create a new region and then decide whether to merge it with overlapping pre-existing one(s)

        region = self.get_region_by_name(region_id)
        line_candidates = defaultdict(list)
        for line in region:
            if line.coords.bbox.right > x_pos:
                # candidate for splitting; look at words
                for word in line:
                    if word.coords.bbox.left > x_pos:
                        # definitely goes in new region
                        line_candidates[line.id].append(word)
                    elif word.coords.bbox.mid_horizontal+(word.coords.bbox.length/4) > x_pos:
                        # could go in new region
                        # ultimate decision could be based on left points of all candidates
                        line_candidates[line.id].append(word)

        if len(line_candidates) == 0:
            return
        #print(line_candidates)
        most_lefts = [] 
        for ml in [x for x in line_candidates.values()]:
            most_lefts.append(min([x.coords.bbox.left for x in ml]))
        median_left = np.median(most_lefts)
        chosen = {}
        for line, words in line_candidates.items():
            filtered_words = [wd for wd in words if wd.coords.bbox.mid_horizontal >= median_left]
            #if len(filtered_words) != len(words):
            #    print(filtered_words,"\t",words)
            if len(filtered_words) > 0:
                chosen[line] = filtered_words
        if len(chosen) == 0:
            return

        new_region_lines = []
        for line_id, words in chosen.items():
            old_line = region.get_line_by_id(line_id)
            
        
        #for line in chosen:
        #    for word in line:



    def split_line_horizontally(self, region_id, line_id, x_pos):

        #print(region_id, self.regions)
        reg = self.get_region_by_name(region_id)
        line = reg.get_line_by_name(line_id)
        xml_line = self.xml_root.xpath(line.xpath)[0]
        new_line = lxml.etree.fromstring(lxml.etree.tostring(xml_line))

        stay_set = set()
        move_set = set()
        new_x_pos = x_pos
        for i, word in enumerate(line):
            this_el = self.xml_root.xpath(word.xpath)
            if word.right < x_pos:
                stay_set.add(this_el[0])
            else:
                this_el = self.xml_root.xpath(word.xpath)
                move_set.add(this_el[0])
                new_x_pos = min(new_x_pos, word.left)

        if len(move_set) == 0:
            return

        parent = xml_line.getparent()
        new_line = lxml.etree.SubElement(parent, xml_line.tag, xml_line.attrib)
        new_line.attrib['id'] += '_s1'
        left_coords, right_coords = self._split_coords(line.coords.parsed, new_x_pos)
        new_coords = lxml.etree.SubElement(new_line, f"{self.xmlns}Coords", points=" ".join([",".join(x) for x in right_coords]))
        new_baseline = lxml.etree.SubElement(new_line, f"{self.xmlns}Baseline", points=line.baseline.raw)

        for s in move_set:
            new_line.append(s)


        #print("")
        #print("After")
        #print(lxml.etree.tostring(xml_line, pretty_print=True))
        #print("Duplicate")
        #print(lxml.etree.tostring(new_line, pretty_print=True))
        exit()
        for m in move_set:
            xml_line.remove(m)
        new_line.attrib['id'] += '_s1'

        xml_line.getparent().append(new_line)
        #print("")
        #print("After")
        #print(lxml.etree.tostring(xml_line, pretty_print=True))
        #print("")
        #print("New...")
        #print(lxml.etree.tostring(new_line, pretty_print=True))
        pass


    @property
    def region_count(self):

        return len(self.regions)

    def get_largest_region(self):

        if len(self.regions) == 0:
            return None
        sorted_regions = sorted([r for r in self], key=lambda x : x.line_count, reverse=True)
        return sorted_regions[0]

    def get_regions_by_line_count(self):

        if len(self.regions) == 0:
            return None
        sorted_regions = sorted([r for r in self], key=lambda x : x.line_count, reverse=True)
        return sorted_regions

    def get_region_by_name(self, region_name):

        if region_name in self.regions_index:
            return self.regions[self.regions_index[region_name]]
        return None

    @property
    def image_file(self):

        return self._image_file

    @property
    def image_height(self):

        return self._image_height

    @property
    def image_width(self):

        return self._image_width

    def get_polygons(self):

        for pt in self._get_points('Coords'):
            yield pt

    def get_baseline_hash(self):

        this_hash = hashlib.md5()
        regions = [r for r in self]
        regions.sort(key=lambda x : x.id)
        for reg in regions:
            this_hash.update(reg.get_region_baseline_hash().hexdigest().encode('utf-8'))

        return this_hash.hexdigest()

    def get_baselines(self):

        for pt in self._get_points('Baseline'):
            yield pt

    def __iter__(self):

        #print("Regions:", self.regions)
        for idx, reg in enumerate(self.regions):
            #print("Reg:", reg)
            reg.iterator_id = f"tr_{idx}"
            yield reg

    def _read_regions(self):

        regions = []
        index = {}
        for x in self.page:
            if x.tag == f"{self.xmlns}TextRegion":
                region_type = "text"
            elif x.tag == f"{self.xmlns}ImageRegion":
                region_type = "image"
            else:
                continue
            reg_lines = []
            reg_id = x.attrib['id']
            reg_xpath = self.xml_original.getpath(x)
            reg_coords = None
            for y in x:
                if y.tag == f"{self.xmlns}Coords":
                    reg_coords = y.attrib['points']
                if y.tag == f"{self.xmlns}TextLine":
                    reg_lines.append(y)
            line_data, line_index = self._read_lines(reg_lines)
            reg_lines = [pageLine(l | {'region_id' : reg_id}) for l in line_data]
            this_reg = pageRegion({'id' : reg_id, 'region_type' : region_type, 'xpath' : reg_xpath, 'Coords' : reg_coords, 'lines' : reg_lines, 'index' : line_index})
            index[reg_id] = len(index)
            regions.append(this_reg)

        return (regions, index)

        '''
        if 'TextRegion' not in self.page:
            return (regions, index)

        text_region = self.page['TextRegion']
        if isinstance(text_region, dict):
            text_region = [text_region]

        for reg in text_region:
            this_reg = pageRegion(reg)
            index[this_reg.id] = len(index)
            regions.append(this_reg)

        return (regions, index)
        '''

    def _read_lines(self, line_data):

        lines = []
        index = {}

        for line in line_data:
            line_id = line.attrib['id']
            line_xpath = self.xml_original.getpath(line)
            line_coords = None
            line_baseline = None
            line_words = []

            for x in line:
                text = ''
                if x.tag == f"{self.xmlns}Coords":
                    line_coords = x.attrib['points']
                if x.tag == f"{self.xmlns}Baseline":
                    line_baseline = x.attrib['points']
                if x.tag == f"{self.xmlns}Word":
                    word_coords, word_text = self._read_words(x)
                    w_xpath = self.xml_original.getpath(x)
                    line_words.append(pageWord({'id' : x.attrib['id'], 'xpath' : w_xpath, 'Coords' : word_coords, 'text' : word_text}))
                if x.tag == f"{self.xmlns}TextEquiv":
                    for z in x:
                        if z.tag == f"{self.xmlns}Unicode":
                            text = z.text
                if text is None:
                    text = ''

            index[line_id] = len(index)
            lines.append({'id' : line_id, 'xpath' : line_xpath, 'Coords' : line_coords, 'Baseline' : line_baseline, 'text' : text, 'words' : line_words})

        return (lines, index)

    def _read_words(self, word_data):

        coords = None
        text = None

        for w in word_data:
            if w.tag == f"{self.xmlns}Coords":
                coords = w.attrib['points']
            if w.tag == f"{self.xmlns}TextEquiv":
                for z in w:
                    if z.tag == f"{self.xmlns}Unicode":
                        text = z.text

        return (coords, text)

    def _get_points(self, points_type):

        page = self.xml['PcGts']['Page']
        if 'TextRegion' not in page:
            print("No text region available")
            return

        text_region = page['TextRegion']
        if isinstance(text_region, dict):
            text_region = [text_region]

        for reg in text_region:
            if 'TextLine' not in reg:
                continue
            text_lines = reg['TextLine']
            reg_id = reg['@id']

            if isinstance(text_lines, dict):
                text_lines = [text_lines]
            for line in text_lines:
                if points_type in line and isinstance(line[points_type], dict):
                    if 'TextEquiv' in line and 'Unicode' in line['TextEquiv']:
                        text = line['TextEquiv']['Unicode']
                    else:
                        text = ''
                    if text is None:
                        text = ''
                    yield({'region_id' : reg_id, 'bounding_box' : parse_coords(line[points_type]['@points'], return_box=True),
                                                 'coords' : parse_coords(line[points_type]['@points'], return_box=False),
                                                 'raw' : line[points_type]['@points'], 'id' : line['@id'], 'text' : text})
#        return
#        for k,v in self.xml['PcGts']['Page'].items():
#            if k == 'TextRegion':
#                if isinstance(v, dict):
#                    if 'TextLine' in v:
#                        region_lines = [v]
#                    else:
#                        print("No text line in dictionary")
#                        return
#
#                elif isinstance(v, list):
#                    region_lines = v
#
#                for reg in region_lines:
#
#                    if isinstance(reg, dict):
#                        lines = [reg]
#                    else:
#                        lines = reg
#                    for ln in lines:
#                        print(ln)
#                        yield(parse_coords(ln['Baseline']['@points']))

if __name__ == '__main__':

    from write_to_page import pageWriter

    PC = pageCoord(QSRRectangle(BoxCoords(left=10, right=50, top=20, bottom=40)))
    print('raw', PC.raw)
    print('parsed', PC.parsed)
    lr = PC.split_horizontal(PC, 30)
    print(lr)
    print(PC.raw_to_box(lr['left']))
    print(PC.raw_to_box(lr['right']))

    xml_file = '../Outputs/Metagrapho/1148/HTR-219785/LAYOUT-138805/7812a7da0eb50898fe3461904ef0b6d8.xml'
    xml_file = "../Outputs/Metagrapho/1148/HTR-123193/LAYOUT-138805/67a97b9fc1d8927688b282d344f713f0.xml"
    xml_file = "../Outputs/Metagrapho/1148/HTR-123193/LAYOUT-138805/88afc09db180a150f9f8b06ecaca07e3.xml"
    xml_file = "../Outputs/Metagrapho/1148/HTR-218533/LAYOUT-138805/74550d2b93db6d0609e4cfe7495ed36a.xml"

    P = pageXML(xml_file)
    #PW.write_to_file("./74550d2b93db6d0609e4cfe7495ed36a.xml")

    #exit()
    for reg in P:
        print(reg)
    print("******")

    P.split_region_horizontal('tr_2', 1200)
    for reg in P:
        print(reg)
    PW = pageWriter(P)
    PW.write_to_file("./74550d2b93db6d0609e4cfe7495ed36a.xml")
    exit()
    R = P.get_largest_region()
    split = R.split_horizontal(1200)
    print(split['left'])
    print(split['right'])

    exit()

    for reg in P:
        print(reg.id, reg)
        #P.split_region_at(reg.id, 100)
        for line in reg:
            print("\t", line)
            split = line.split_horizontal(700)
            print(split)
            exit()
        print("")

    #P.split_region_vertically('tr_2', 700)
    P.split_region_horizontally('tr_2', 700)
    exit()

    for reg in P:
        print(reg.id, reg)
        #P.split_region_at(reg.id, 100)
        for line in reg:
            print("\t", line)
        print("")



