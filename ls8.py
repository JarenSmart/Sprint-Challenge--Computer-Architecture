#!/usr/bin/env python3

"""Main."""

from cpu import *
import sys
error_running = """
Error: You must specify a file name as a command line argument.
    Please run using:
        python3 ls8.py sctest.ls8
"""


if len(sys.argv) != 2:
    print(error_running)
    sys.exit(1)
else:
    # python3 ls8.py sctest.ls8
    file_name = sys.argv[1]

cpu = CPU()
cpu.load(file_name)
cpu.run()
