# pads2step
Converts PADS .d PCB decal files to STEP .stp format. Allows easy transfer from electrical to mechanical layouts.

It's easy to find people complaining about the lack of communication between "electrical land" and "mechanical land" when it comes to device layout, but much harder to find tools meant to actually make that communication easier - especially tools that don't require massive, proprietary CAD packages to make it happen. Hopefully this helps!

This script takes a PADS .d file, reads each line into a Python object, and then spits it out as a sketch in a STEP .stp file. I don't know if there is any demand for the reverse operation or conversion from other PADS objects to .stp format, but it should be doable. Thankfully, the PADS file format is much simpler than STEP.

This is my first open-source project, and it's currently a mess! All suggestions and pull requests are welcome.
