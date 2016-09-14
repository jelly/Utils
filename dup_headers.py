#!/usr/bin/python

# Script which scans for duplicate #include headers in a file.

import sys

includes = []
cpp_file = sys.argv[1]
for line in open(cpp_file, 'r'):
    if not '#include' in line:
        continue

    # Strip newlines, etc.
    line = line.strip()

    if line in includes:
        print("Duplicate line %s in %s" % (line, cpp_file))
    else:
        includes.append(line)


