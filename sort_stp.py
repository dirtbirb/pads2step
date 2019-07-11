#!/usr/bin/python

# Extracts data entities from an stp file and sorts them by number

f, f_keys = [], []

# Get all data entities
fn = "examples/test_sketch.stp"
with open(fn) as stp:
    for line in stp:
        # Reconnect broken lines
        while len(line) > 3 and line[-3] != ';':
            line = line[:-2]
            line += next(stp)

        # Save all data entities and their numbers
        if line[0] == '#' and '=' in line:
            stop = line.find('=')
            f.append(line)
            f_keys.append(int(line[1:stop]))

# Sort all data entities by their number
f = [x for _, x in sorted(zip(f_keys, f), key=lambda pair: pair[0])]

# Output result
with open("examples/test_sketch_out.txt", 'w') as out:
    prev = 0
    for line in f:
        out.write(line)
