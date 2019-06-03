#!/usr/bin/env python-real
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys

from radiomics.scripts import parse_args

if __name__ == '__main__':
  if sys.argv[1] == '--xml' or sys.argv[1] == '-x':
    with open(__file__[:-6] + '.xml', 'r') as xmlFP:  # Cut off "Script" from filename
      print(xmlFP.read())
  else:
    # Check if old-style label argument is provided
    if '--label' in sys.argv:
      label_idx = sys.argv.index('--label')
      # get the value for the label
      label = sys.argv[label_idx + 1]
      # Remove the old-style command argument and value
      sys.argv.pop(label_idx + 1)
      sys.argv.pop(label_idx)

      # append new style
      sys.argv.append('--setting=label:' + label)

    sys.argv.append('--format=csv')  # Append this format to ensure a csv return format (default is txt)
    sys.argv.append('--verbosity=4')  # Print out logging with level INFO and higher
    sys.argv.append('--setting=correctMask:True')
    parse_args()  # Entry point for the "pyradiomics" script
