#!/usr/bin/python

from datetime import datetime   # Date and time representation
import sys
import math

def spliterator(line, sep=' ', filt=''):
    ''' Split a line, drop empty segments, return a filtered list of results '''

    def filterator(string):
        return string != filt

    return filter( filterator, line.rstrip().split(sep) )

# PADS entities ---------------------------------------------------------------

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
            elif i == 1 or i > 2:
                attr = int(header[i])
            elif i == 2: attr = float(header[i])
            setattr(self, items[i], attr)

        # Read piece body
        self.segments = []
        for i in range(self.numcoord):
            segments = spliterator(next(infile).rstrip())
            l = len(segments)
            if l == 2:
                self.shape = "line"
            elif l == 8:
                self.shape = "arc"
            else:
                print("ERROR: Wrong number of piece coordinates: " + l)
                break

            seg_iter = iter(segments)
            for seg in seg_iter:
                self.segments.append( (float(seg), float(next(seg_iter))) )

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


# PADS file types -------------------------------------------------------------

class PadsItem(object):
    def __init__(self, infile):
        print("This file type is not supported")

class DraftingItem(PadsItem):
    pass

class SchematicDecals(PadsItem):
    pass

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
        while spliterator(line)[0] in ('OPEN', 'CLOSED', 'CIRCLE', 'COPOPN', 'COPCLS', 'COPCIR', 'BRDCUT', 'BRDCCO', 'KPTCLS', 'KPTCIT', 'TAG'):
            self.pieces.append( Piece(line, infile) )
            line = next(infile).rstrip()

        # Skip text definitions
        self.text = []
        while line[0] != 'T':
            line = next(infile)

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


# STEP writer -----------------------------------------------------------------

def pads2step(pads):
    ''' Write out .stp file.
    Use double-quotes for everything here, .stp uses single quotes.
    '''

    with open(pads.name + '.stp', 'w') as stp:

        class j(): j=1  # Hack, necessary to keep j in this scope

        def write(line):
            ''' Take a line, add ";\n", write it out, increment j '''
            stp.write(line + ";\n")
            j.j += 1

        def var(item):
            ''' Take an item, return it as '#item' '''
            return "#{0}".format(item)

        def var_list(*items):
            ''' Take a bunch of items, return '(#item1,#item2,#item3,...)' '''
            return ','.join(map(var, items))

        def vect(a, b):
            dist = b-a
            if dist > 0:
                return '1'
            elif dist == 0:
                return '0'
            else:
                return '-1'

        def write_shape_end(w):
            write( var(j.j) + "=PRESENTATION_STYLE_ASSIGNMENT((#{0}))".format(j.j-1) )
            write( var(j.j) + "=STYLED_ITEM('',(#{0}),#{1})".format(j.j-1, j.j-3) )
            ret = j.j
            write( var(j.j) + "=COMPOSITE_CURVE_SEGMENT(.CONTINUOUS.,.T.,#{0})".format(j.j-4) )
            write( var(j.j) + "=CURVE_STYLE('',#{0},POSITIVE_LENGTH_MEASURE({1}),#5)".format(j_font, w) )
            return ret

        def write_line(x0, y0, w, seg):
            x, y, = seg
            d = math.sqrt((x-x0)**2 + (y-y0)**2)

            if x0 != x and y0 != y: print(y0, y)
            write( "#{0}=DIRECTION('',({1},{2},0.E0))".format(j.j, vect(x0,x), vect(y0,y)))
            write( "#{0}=VECTOR('',#{1},{2})".format(j.j, j.j-1, d) )
            write( "#{0}=CARTESIAN_POINT('',({1},{2},0.E0))".format(j.j, x0,y0) )
            write( "#{0}=LINE('',#{1},#{2})".format(j.j, j.j-1,j.j-2) )
            write( "#{0}=TRIMMED_CURVE('',#{1},(PARAMETER_VALUE(0.E0)),(PARAMETER_VALUE(1.E0)),.T.,.UNSPECIFIED.)".format(j.j, j.j-1) )
            return write_shape_end(w)

        def write_arc(x0, y0, w, seg):
            x, y, ab, aa, ax1, ay1, ax2, ay2, = seg
            r = (ax2-ax1)/2
            xc, yc = (ax2 + ax1)/2, (ay2 + ay1)/2

            write( "#{0}=CARTESIAN_POINT('',({1},{2},0.E0))".format(j.j, xc, yc) )
            write( "#{0}=DIRECTION('',(0.E0,0.E0,1.E0))".format(j.j) )
            write( "#{0}=DIRECTION('',({1},{2},0.E0))".format(j.j, vect(x0,x), vect(y0,y)) )
            write( "#{0}=AXIS2_PLACEMENT_3D('',{1})".format(j.j, var_list(j.j-3,j.j-2,j.j-1)) )
            write( "#{0}=CIRCLE('',#{1},{2})".format(j.j, j.j-1, r) )
            write( "#{0}=TRIMMED_CURVE('',#{1},(PARAMETER_VALUE({2})),(PARAMETER_VALUE({3})),.T.,.UNSPECIFIED.)".format(j.j, j.j-1, ab, aa) )
            return write_shape_end(w)

        def write_comp(*items):
            ret = j.j
            write( var(j.j) + "=COMPOSITE_CURVE(''," + var_list(*items) + ",.F.)")
            return ret

        def write_shape(shape):
            w = float(shape.width)
            x0, y0, = shape.segments[0]
            segs = []
            for seg in shape.segments[1:]:
                l = len(seg)
                if l == 2:      # Line
                    segs.append( write_line(x0, y0, w, seg) )
                elif l == 8:    # Arc
                    segs.append( write_arc(x0, y0, w, seg) )
                else:           # ?
                    print("ERROR: writing segment that isn't line or arc")
                    break
                x0, y0, = seg
            return write_comp(*segs)

        def write_circle(shape):
            w = shape.width
            x0, y0, = shape.segments[0]
            x1, y1, = shape.segments[1]
            xc, yc = (x0 + x1)/2, (y0 + y1)/2
            r = abs(xc - x0)
            ax1, ay1 = xc-r, yc-r
            ax2, ay2 = xc+r, yc+r

            a = write_arc(x0, y0, w, [x1, y1, 0, 180, ax1, ay1, ax2, ay2])
            b = write_arc(x1, y1, w, [x0, y0, 180, 180, ax1, ay1, ax2, ay2])
            return write_comp(a, b)

        w_default = 0.02
        def write_pad_circle(x, y, r):
            w = w_default
            x0, y0 = x-r, y
            x1, y1 = x+r, y
            ax1, ay1 = x-r, y-r
            ax2, ay2 = x+r, y+r

            a = write_arc(x0, y0, w, [x1, y1, 0, 180, ax1, ay1, ax2, ay2])
            b = write_arc(x1, y1, w, [x0, y0, 180, 180, ax1, ay1, ax2, ay2])
            return write_comp(a, b)

        def write_pad_rectangle(x, y, r, corner, ori, l, offset):
            # TODO: support rounded/chamfered corners
            # TODO: offset??

            w = w_default
            r = r/2
            l = l/2

            sin, cos = math.sin(math.radians(ori)), math.cos(math.radians(ori))
            x_f, y_f = r*sin + l*cos, r*cos + l*sin

            x_l, x_r = x-x_f, x+x_f
            y_t, y_b = y+y_f, y-y_f

            a = write_line(x_l, y_t, w, (x_r, y_t)) # Top
            b = write_line(x_r, y_t, w, (x_r, y_b)) # Right
            c = write_line(x_r, y_b, w, (x_l, y_b)) # Bottom
            d = write_line(x_l, y_b, w, (x_l, y_t)) # Left
            return write_comp(a, b, c, d)

        def write_pad_square(x, y, r):
            return write_pad_rectangle(x, y, r, 0, 0, r, 0)

        def write_pad_oval(x, y, r, ori, l, offset):
            # TODO: offset???

            w = w_default
            r = r/2
            l = l/2 - r
            sin, cos = math.sin(math.radians(ori)), math.cos(math.radians(ori))
            x_f, y_f = (r*sin + l*cos), (r*cos + l*sin)

            x_l, x_r = x-x_f, x+x_f
            y_t, y_b = y+y_f, y-y_f

            ax1_1, ay1_1 = x_r-r, y_b
            ax2_1, ay2_1 = x_r+r, y_t

            ax1_2, ay1_2 = x_l-r, y_b
            ax2_2, ay2_2 = x_l+r, y_t

            a = write_line(x_l, y_t, w, (x_r, y_t)) # Top
            b = write_arc(x_r, y_t, w, [x_r, y_b, 0, 180, ax1_1, ay1_1, ax2_1, ay2_1]) # Right
            c = write_line(x_r, y_b, w, (x_l, y_b)) # Bottom
            d = write_arc(x_l, y_b, w, [x_l, y_t, 0, 180, ax1_2, ay1_2, ax2_2, ay2_2]) # Left
            return write_comp(a, b, c, d)

        def write_pad_annular(x, y, r_out, r_in):
            a = write_pad_circle(x, y, r_out)
            b = write_pad_circle(x, y, r_in)
            return write_comp(a, b)

        j = j()

        # Begin header
        write("ISO-10303-21")
        write("HEADER")

        # FILE_DESCRIPTION
        description = 'Converted drawing from pads file' # Informal description
        conformance = '2;1' # Conformance level to ISO-10303-21

        write("FILE_DESCRIPTION(('"
            + description + "'),'"
            + conformance + "')")

        # FILE_NAME
        name = pads.name
        timestamp = [
            str(pads.timestamp.year),
            str(pads.timestamp.month),
            str(pads.timestamp.day) + 'T' + str(pads.timestamp.hour),
            ':' + str(pads.timestamp.minute),
            ':' + str(pads.timestamp.second) ]
        timestamp = '-'.join(timestamp)
        author = 'PADS2STEP'
        organization = 'Distant Focus Corporation'
        preprocessor_version = 'pads2step.py'
        originating_system = ''
        authorization = ''

        write("FILE_NAME('"
            + name + "','"
            + timestamp + "',('"
            + author + "'),('"
            + organization + "'),'"
            + preprocessor_version + "','"
            + originating_system + "','"
            + authorization + "'")

        # FILE_SCHEMA
        schema = "'AUTOMOTIVE_DESIGN \{ 1 0 10303 214 1 1 1 1 \}'"
        write( "FILE_SCHEMA(('" + schema + "'))" )

        # End header
        write("ENDSEC")

        # Begin data section
        write("DATA")
        j.j = 1

        # Colors
        colors = (  # name, R, G, B
            ('',0.E0,0.E0,6.6E-1),
            ('',0.E0,6.6E-1,0.E0),
            ('',3.4E-1,3.3E-1,3.5E-1),
            ('',3.9E-1,5.6E-1,8.1E-1),
            ('',4.E-1,4.509803921569E-1,1.E0),
            ('',4.4E-1,5.E-1,5.5E-1),
            ('',5.09804E-1,5.09804E-1,5.09804E-1),
            ('',6.E-1,4.E-1,2.E-1),
            ('',6.952E-1,7.426E-1,7.9E-1),
            ('',8.03922E-1,5.88235E-1,1.96078E-1),
            ('',8.4E-1,3.3E-1,3.5E-1),
            ('',8.8E-1,1.6E-1,1.6E-1),
            ('',8.784E-1,9.49E-1,1.E0) )
        for color in colors:
            write(var(j.j) + "=COLOUR_RGB" + str(color))

        # Origin
        write( var(j.j) + "=CARTESIAN_POINT('',(0.E0,0.E0,0.E0))" )
        write( var(j.j) + "=DIRECTION('',(0.E0,0.E0,1.E0))" )
        write( var(j.j) + "=DIRECTION('',(1.E0,0.E0,0.E0))" )
        j_axis = j.j
        write( var(j.j) + "=AXIS2_PLACEMENT_3D(" + var_list('DEFAULT_CSYS',j.j-3,j.j-2,j.j-1) )
        j_font = j.j   # This is referenced frequently
        write( var(j.j) + "=DRAUGHTING_PRE_DEFINED_CURVE_FONT('continuous')" )
        write( var(j.j) + "=CURVE_STYLE(''," + var(j.j-1) + ",POSITIVE_LENGTH_MEASURE(2.E-2),#8)" )
        write( var(j.j) + "=PRESENTATION_STYLE_ASSIGNMENT((" + var(j.j-1) + "))" )
        write( var(j.j) + "=STYLED_ITEM(''," + var_list(j.j-1) + "," + var(j_font) + ")" )

        # Shapes
        shapes = []
        if shape_flag:
            for piece in pads.pieces:
                t = piece.type
                if t in ("OPEN", "CLOSED", "COPOPN", "COPCLS", "KPTCLS", "BRDCUT", "BRDCCO"):
                    shapes.append( write_shape(piece) )
                elif t in ("CIRCLE", "COPCIR", "KPTCIR"):
                    shapes.append( write_circle(piece) )

        # Find default pad stack for terminals
        for pad in pads.pads:
            if pad.pin == 0:
                pad_0 = pad
                break
        else: print("No pad 0 found!")

        # Terminals
        for i in range(1,len(pads.terminals)+1):

            # Find matching pad stack
            for stack in pads.pads:
                if stack.pin == i:
                    stack_match = stack
                    break
            else: stack_match = pad_0

            # Get top layer
            for layer in stack_match.layers:
                if layer.n == -2:
                    layer_match = layer
                    break
            else: print("No top layer found for pin {0}!".format(i-1))

            # Write drill hole
            x, y = pads.terminals[i-1][0][0], pads.terminals[i-1][0][1]
            if stack_match.drill > 0:
                if hasattr(stack_match, 'drllen'):
                    shapes.append( write_pad_oval(x, y, stack_match.drill, stack_match.drlori, stack_match.drllen, stack_match.drloff))
                else:
                    shapes.append( write_pad_circle(x, y, stack_match.drill) )

            # Write appropriate shape
            if layer_match.shape in ('R', 'RA', 'RT'):
                shapes.append( write_pad_circle(x, y, layer_match.width) )
            elif layer_match.shape in ('S', 'SA', 'ST'):
                shapes.append( write_pad_square(x, y, layer_match.width) )
            elif layer_match.shape == 'A':
                shapes.append( write_pad_annular(x, y, layer_match.width, layer_match.intd) )
            elif layer_match.shape == 'OF':
                shapes.append( write_pad_oval(x, y, layer_match.width, layer_match.ori, layer_match.length, layer_match.offset) )
            elif layer_match.shape == 'RF':
                shapes.append( write_pad_rectangle(x, y, layer_match.width, layer_match.corner, layer_match.ori, layer_match.length, layer_match.offset) )
            else: print("WARNING: Skipped unrecognized pad shape {0}".format(layer_match.shape))

        # Finish shapes
        j_set = j.j
        write( "#{0}=GEOMETRIC_SET('',{1})".format(j.j, var_list(*shapes)) )

        # Footer
        write( "#{0}=PRESENTATION_LAYER_ASSIGNMENT('.BLACK_HOLE','',(#{1}))".format(j.j,j_axis) )
        write( "#{0}=INVISIBILITY((#{1}))".format(j.j,j.j-1) )
        write( "#{0}=(LENGTH_UNIT()NAMED_UNIT(*)SI_UNIT(.MILLI.,.METRE.))".format(j.j) )
        write( "#{0}=(NAMED_UNIT(*)PLANE_ANGLE_UNIT()SI_UNIT($,.RADIAN.))".format(j.j) )
        write( "#{0}=PLANE_ANGLE_MEASURE_WITH_UNIT(PLANE_ANGLE_MEASURE(1.745329251994E-2),#{1})".format(j.j,j.j-1) )
        write( "#{0}=(CONVERSION_BASED_UNIT('DEGREE',#{1})NAMED_UNIT(*)PLANE_ANGLE_UNIT())".format(j.j,j.j-1) )
        write( "#{0}=(NAMED_UNIT(*)SI_UNIT($,.STERADIAN.)SOLID_ANGLE_UNIT())".format(j.j,) )
        write( "#{0}=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.477113140796E-3),#{1},'distance_accuracy_value','Maximum model space distance between geometric entities at asserted connectivities')".format(j.j,j.j-5) )
        write( "#{0}=(GEOMETRIC_REPRESENTATION_CONTEXT(3)GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#{1}))GLOBAL_UNIT_ASSIGNED_CONTEXT({2})REPRESENTATION_CONTEXT('ID1','3'))".format(j.j,j.j-1,var_list(j.j-6, j.j-3, j.j-2)) )
        write( "#{0}=GEOMETRICALLY_BOUNDED_SURFACE_SHAPE_REPRESENTATION('',(#{1}),#{2})".format(j.j,j_set,j.j-1) )
        write( "#{0}=MECHANICAL_DESIGN_GEOMETRIC_PRESENTATION_REPRESENTATION('',({1}),#{2})".format(j.j,var_list(*shapes),j.j-2) )

        write("ENDSEC")
        write("END-ISO-10303-21")


# main ------------------------------------------------------------------------

if len(sys.argv) not in range(2, 4) or '-h' in sys.argv:
    print('pads2step.py: this tool converts .d decal files from PADS into .stp format.\n'
        + 'Usage: pads2step.py <pads filename> <flags>\n'
        + 'Flags:\n'
        + "-h: show this message, don't convert anything\n"
        + '-x: exclude part detail, only show pin pads and drill holes')
    sys.exit()

fn = sys.argv[1]
if '-x' in sys.argv: shape_flag = False
else: shape_flag = True

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
pads2step(thing)

if False:#__name__ == "__main__":
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
