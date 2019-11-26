# pads2step
Converts PADS .d PCB decal files to STEP .stp format. Allows easy transfer of connector footprints from electrical to mechanical layouts.

Usage: pads2step.py [options] <filename>.d

Options:  
-h:     Show usage directions  
-x:     Exclude connector body drawings, only output drill holes and terminal pads  

It's easy to find people complaining about the lack of communication between "electrical land" and "mechanical land" when it comes to device layout, but much harder to find tools meant to actually make that communication easier - especially tools that don't require massive, proprietary CAD packages to make it happen. Hopefully this helps!

This script takes a PADS .d file, reads each line into a Python object, and then spits it out as a sketch in a STEP .stp file. I don't know if there is any demand for the reverse operation or conversion from other PADS objects to .stp format, but it should be doable. Thankfully, the PADS file format is much simpler than STEP.

This is my first open-source project, and it's currently a mess! Currently works for my purposes, which are limited. All suggestions, feature requests, and contributions are welcome.
