#!/usr/bin/python

from datetime import datetime

def spliterator(line, sep=' ', filt=''):
    ''' Split a line, drop empty segments, return an iterator of results '''

    def filterator(string):
        return string != filt

    return filter( filterator, line.rstrip().split(sep) )

class PadsItem(object):
    pass

class DraftingItem(PadsItem):
    def __init__(self, infile):
        # Skip line
        next(infile)

        # Read header data
        header = next(infile).split(' ')

        # Remove empty entries
        for item in header:
            if item == '': del item

        # Save header data
        self.name =         header[0]
        self.linetype =     header[1]
        self.units =        header[2]
        self.x, self.y =    header[3], header[4]
        self.pieces =       header[5]
        self.text =         header[6]

        # Read timestamp
        timestamp = next(infile).split('.')
        self.timestamp = datetime(*timestamp)

        # Read pieces
        for line in infile:
            pass
            # Read piece header


            # Read piece corners
        # Read text

class SchematicDecals(PadsItem):
    pass







class AttributeLabel(object):
    def __init__(self, line1, line2):
        items = ( 'x', 'y', 'rotation', 'mirror', 'height', 'width', 'layer',
            'just', 'flags', 'font_info' )

        vals = spliterator(line1)
        for i in range(len(vals)):
            if i < 3 or i == 4 or i == 5: item = float(vals[i])
            elif i == 3 or (i > 5 and i < 9): item = int(vals[i])
            elif i == 9:
                item = ''
                for j in range(i, len(vals)):
                    item += vals[j] + ' '
                setattr(self, items[i], item[:-1].replace('\"', ''))
                break
            setattr(self, items[i], item)

        self.name = line2

class Piece(object):
    def __init__(self, line, infile):
        # Read piece header
        items = ( 'type', 'numcoord', 'width', 'layer', 'linestyle' )
        header = spliterator(line)
        for i in range(len(header)):
            if i == 0: attr = header[i]
            elif i == 1 or i > 2: attr = int(header[i])
            elif i == 2: attr = float(header[i])
            setattr(self, items[i], attr)

        # Read piece body
        self.coords = []
        for i in range(self.numcoord):
            coords = spliterator(next(infile).rstrip())
            l = len(coords)
            if l == 2:
                self.shape = "line"
            elif l == 8:
                self.shape = "arc"
            else:
                print("ERROR: Wrong number of piece coordinates: " + l)
                break

            for coord in coords:
                self.coords.append(float(coord))

class Terminal(list):
    def __init__(self, line):
        items = iter(spliterator(line))
        self.append( (float(next(items).replace('T', '')), float(next(items)) ) )
        self.append( (float(next(items)), float(next(items)) ) )
        self.pin = next(items)

class PadStack(object):
    def __init__(self, line, infile):
        class Layer(object):
            def __init__(self, line):
                items = iter(spliterator(line))
                self.n = int(next(items))
                self.width = float(next(items))
                self.shape = next(items)
                if self.shape == 'S':       # Square normal pad
                    self.corner = float(next(items))
                elif self.shape == 'A':     # Annular pad
                    self.intd = float(next(items))
                elif self.shape == 'OF':    # Oval finger pad
                    self.ori = float(next(items))
                    self.length = float(next(items))
                    self.offset = float(next(items))
                elif self.shape == 'RF':    # Rectangular finger pad
                    self.corner = float(next(items))
                    self.ori = float(next(items))
                    self.length = float(next(items))
                    self.offset = float(next(items))
                elif self.shape == 'RT' or self.shape == 'ST':
                    self.ori = float(next(items))
                    self.intd = float(next(items))
                    self.spkwid = float(next(items))
                    self.n_spk = int(next(items))

        # Read header line
        items = ('pin', 'n_layers', 'plated', 'drill', 'drlori', 'drllen', 'drloff')
        header = spliterator(line)[1:]
        self.slotted = len(header) > 4
        for i in range(len(header)):
            if i < 2: attr = int(header[i])
            elif i == 2: attr = header[i]
            elif i > 2: attr = float(header[i])
            setattr(self, items[i], attr)

        # Read layers
        self.layers = []
        for i in range(self.n_layers):
            self.layers.append( Layer(next(infile)) )


class PCBDecals(PadsItem):

    def __init__(self, infile):
        # Read header line as an iterator, dropping empty strings
        header = spliterator(next(infile).rstrip())

        # Save header data
        header_attrs = ( 'name', 'units', 'x', 'y', 'n_attrs', 'n_labels',
            'n_pieces', 'n_text', 'n_terminals', 'n_stacks', 'maxlayers' )
        for i in range(len(header)):
            if i == 0 or i == 1: attr = header[i]
            if i == 2 or i == 3: attr = float(header[i])
            if i > 3: attr = int(header[i])
            setattr(self, header_attrs[i], attr)

        # Read timestamp
        timestamp = next(infile).rstrip().split(' ')[1].split('.')
        self.timestamp = datetime( *list(map(int, timestamp)) )

        # Read attributes
        self.attributes = {}
        line = next(infile).rstrip()
        while line[0] == '\"':
            attribute = line[1:].split('\" ')
            self.attributes[attribute[0]] = attribute[1]
            line = next(infile).rstrip()

        # Read attribute labels
        self.attribute_labels = []
        while line[-1] == '\"':
            self.attribute_labels.append( AttributeLabel(line, next(infile).rstrip()) )
            line = next(infile).rstrip()

        # Read piece definitions
        self.pieces = []
        while line[0] != 'T':
            self.pieces.append( Piece(line, infile) )
            line = next(infile).rstrip()

        # Read text definitions?

        # Read terminals
        self.terminals = []
        while line[0] == 'T':
            self.terminals.append( Terminal(line) )
            line = next(infile).rstrip()

        # Read pad stacks
        self.pads = []
        while line[0:3] == 'PAD':
            self.pads.append( PadStack(line, infile) )
            line = next(infile).rstrip()


class PartTypes(PadsItem):
    pass


fn = "examples/MOLEX_1051330011.d"
thing = None
with open(fn) as infile:
    # Get data type, skip blank line
    line = next(infile).rstrip()
    next(infile)

    # Check if data type recognized
    if line == "*PADS-LIBRARY-LINE-ITEMS-V9*":
        thing = DraftingItem(infile)
    elif line == "*PADS-LIBRARY-SCH-DECALS-V9*":
        thing = SchematicDecals(infile)
    elif line == "*PADS-LIBRARY-PCB-DECALS-V9*":
        thing = PCBDecals(infile)
    elif line == "*PADS-LIBRARY-PART-TYPES-V9*":
        thing = PartTypes(infile)
    else: # Invalid data type
        print("Unrecognized data type!")

if __name__ == "__main__":
    print("TESTS:")
    tests = [
        ('name', 'MOLEX_1051330011'),
        ('units', 'M'),
        ('x', 0),
        ('y', 0),
        ('n_attrs', 2),
        ('n_labels', 3),
        ('n_pieces', 7),
        ('n_text', 0),
        ('n_terminals', 8),
        ('n_stacks', 4),
        ('maxlayers', 0),
        ('timestamp', datetime(2017, 10, 26, 14, 12, 31))
    ]
    for t in tests:
        print(str(getattr(thing, t[0]) == t[1]) + ' - ' + t[0] + ": " + str(t[1]))

    print(thing.attributes["Geometry.Height"])

    for lbl in thing.attribute_labels:
        print(lbl.name, lbl.y, int(lbl.flags))

    for pc in thing.pieces:
        print(pc.type)

    for t in thing.terminals:
        print(t.pin)

    for p in thing.pads:
        print(p.plated)
        for l in p.layers:
            print(l.shape)
