#!/usr/bin/env python3
"""Usage: python3 gen_schematic.py <spec_module>   e.g. board_p_spec"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schgen_core

spec = importlib.import_module(sys.argv[1])
schgen_core.generate(spec)
