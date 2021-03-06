#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Example plugin for ogtools, lists document canvases and contents of config file.

To run:

$ ogtool run-plugin example_plugin ./tests/color-test.graffle  --config=ogplugins/example_plugin.yaml --canvas my-canvas -vvv
"""


def main(document, config, canvas=None):
    print 'example plugin'
    print "canvas", canvas
    print "canvases in document:"
    for c in document.canvases():
        print c.name()

    print repr(config)
