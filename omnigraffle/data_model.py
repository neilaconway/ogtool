#!/usr/bin/env python
"""
The OmniGraffle document data model, for traversing all elements in the
document, e,g, to extract or inject text.
"""
from __future__ import print_function

from functools import partial

import appscript


DEBUG_MODE = False


def debug(level, *args):
    if DEBUG_MODE:
        print("|   " * level, *args)


class Item(object):
    """
    An item in an OmniGraffle document.

    May be Named and/or a TextContainer.
    """
    elements = []
    _current_canvas_name = ''

    def __init__(self, item):
        self.item = item

    def walk(self, callback, skip_invisible_layers=False, nodes_visited=None, level=0):
        """
        Traverse the a document tree and invoke callback on each element.
        # TODO: apparently some elements are visited more than once, others are never visited
        """
        debug = partial(globals()['debug'], level)

        # prevent visited nodes from being visited again:
        if not nodes_visited:
            nodes_visited = set()  # init not cache
        try:
            if self.item.id() in nodes_visited:
                return
            else:
                nodes_visited.add(self.item.id())
        except appscript.reference.CommandError:
            pass  # elements without id cannot be tracked

        if isinstance(self, Canvas):
            debug("\n\n-----------------Canvas %s\n-----------------\n\n" % self.item.name())
            Item._current_canvas_name = self.item.name()
        if isinstance(self, Layer):
            if skip_invisible_layers and not self.item.visible():
                return  # skip invisible layers

        debug('::::', self.item_info())

        callback(self)

        for class_name in self.elements:
            klass = globals()[class_name]
            collection = getattr(self.item, klass.collection)
            try:
                collection()
            except appscript.reference.CommandError:
                # apparently there's a problem with some collections, e.g. 'IncomingLine' in Graphics
                continue

            debug("+--- processing collection", class_name, len(collection()))
            for idx, item in enumerate(collection()):
                debug("   ", class_name, "#", idx)
                i = klass(item)
                i.walk(callback, skip_invisible_layers, nodes_visited, level + 1)

    def item_info(self):
        return "(%s) %s == %s (%s...)" % (self.id, self.class_, self.name, self.text[:20])

    @property
    def canvas_name(self):
        # this is not thread-safe!
        return Item._current_canvas_name

    @property
    def properties(self):
        # this is not thread-safe!
        return self.item.properties()

    @properties.setter
    def properties(self, value):
        self.item.properties.set(value)

    @property
    def class_(self):
        try:
            return self.item.class_()
        except appscript.reference.CommandError:
            return None

    @property
    def id(self):
        try:
            return self.item.id()
        except appscript.reference.CommandError:
            return 'no id'

    @property
    def text(self):
        try:
            return self.item.text()
        except appscript.reference.CommandError:
            return ''

    @property
    def name(self):
        try:
            return self.item.name()
        except appscript.reference.CommandError:
            return ''


class Named(object):
    @property
    def name(self):
        return self.item.name()

    @name.setter
    def name(self, value):
        self.item.name.set(value)


class Filled(object):
    @property
    def fill_color(self):
        return self.item.fill_color()

    @fill_color.setter
    def fill_color(self, value):
        self.item.fill_color.set(value)


class HasStroke(object):
    @property
    def stroke_color(self):
        return self.item.stroke_color()

    @stroke_color.setter
    def stroke_color(self, value):
        self.item.stroke_color.set(value)


class TextContainer(object):
    @property
    def text(self):
        return self.item.text

    @text.setter
    def text(self, value):
        self.item.text.set(value)


class Document(Item):
    elements = ['Canvas']


class Canvas(Item, Named):
    collection = 'canvases'
    elements = ['Layer', 'Graphic', 'Group', 'Line', 'Shape', 'Solid', 'Subgraph']
    # elements = ['Layer'] # TODO: are all objects in layers?


class Layer(Item):
    collection = 'layers'
    elements = ['Graphic', 'Group', 'Line', 'Shape', 'Solid', 'Subgraph']


class TableSlice(Item):
    """A row or column of a table."""
    collection = 'table_slices'
    elements = ['Group']  # TODO: what else?'?


class Column(Item):
    collection = 'columns'
    elements = ['Group']  # TODO: what else?'?


class Row(Item):
    collection = 'rows'
    elements = ['Group', 'Graphic']  # TODO: what else?'?


class Graphic(Item, HasStroke):  # Group', 'Line', 'Solid
    collection = 'graphics'
    elements = ['IncomingLine', 'Line', 'OutgoingLine']  # TODO: also contains "user data items', 'what is that?'"


class Group(Graphic):
    collection = 'groups'
    # TODO: graphics might be enough to enumerate, subgraphs and tables are also groups
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']


class IncomingLine(Graphic):
    collection = 'incoming_lines'


class Line(Graphic):
    collection = 'lines'
    elements = ['Label']


class OutgoingLine(Graphic):
    collection = 'outgoing_lines'


class Solid(Graphic, Filled, TextContainer):  # Polygon', 'Shape
    collection = 'solids'


class Shape(Solid, Named):
    collection = 'shapes'


class Label(Shape, Named):
    collection = 'labels'


class Subgraph(Group):
    collection = 'subgraphs'
    elements = ['Graphic', 'Group', 'Shape', 'Solid', 'Subgraph']


class Table(Group):
    collection = 'tables'
    elements = ['Column', 'Row']
