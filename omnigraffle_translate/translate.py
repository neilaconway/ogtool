#!/usr/bin/env python

import argparse
import codecs
from collections import defaultdict
from functools import partial
import os
import shutil
import sys

import appscript
import polib


from omnigraffle_export.omnigraffle_command import OmniGraffleSandboxedCommand

from data_model import Canvas, TextContainer

"""
Translation of Omnigrafle files

1. Create Translation memory
    - get all cavases in file
    - for each canvas: get all text objects and dump to pot-file

2. Update translatiosn
    - create a copy of OmniGraffle source file language suffix
    - read po-file and make a translation dictionary d[msgid] = msgstr
        (replace newlines and quotes!!)
    - walk through all objects, if text: replace with translated text
    - save

TODO: how to make sure OmniGraffle files are not changed between exporting pot and tranlsation? 
    Create dedicated image repo (needs branchens for each resource release) or add to the repo
     where illustrations are used (adds lots of duplication)

Do we need keys and template files?

    - create a key (hash) for each text
    - create a omnigraffle template file where texts are replaced by hashes
    - copy templates and fill in translations template files

""" 

class OmniGraffleSandboxedTranslator(OmniGraffleSandboxedCommand):
    """Translator for OmniGraffle6"""

    def cmd_extract_translations(self):
        """Extract translations from an OmniGraffle document to a POT file."""
        self.open_document()

        def extract_translations(file_name, canvas_name, translation_memory, element):
            if isinstance(element, TextContainer):
                # add text to memory
                location = "%s/%s" % (file_name, canvas_name)
                translation_memory[element.item.text()].add(location)

        file_name = os.path.basename(self.args.source)
        translation_memory = defaultdict(set)
        for canvas in self.doc.canvases():
            c = Canvas(canvas)
            c.walk(partial(extract_translations, file_name, canvas.name(), translation_memory))

        self.og.windows.first().close()
        self.dump_translation_memory(translation_memory)

    def dump_translation_memory(self, tm):

        pot = polib.POFile()
        
        for text in sorted(tm.keys()):
            entry = polib.POEntry(
                msgid=text,
                msgstr=text,
                occurrences=[(location, '0') for location in tm[text]]
            )
            pot.append(entry)
        pot.save(os.path.splitext(self.args.source)[0]+'.pot')


    def cmd_translate(self):
        """Inject translations from a po-file into an OmniGraffle document."""

        tm = self.read_translation_memory(self.args.po_file)


        root, ext = os.path.splitext(self.args.document)
        translated_copy = root + '-' + self.args.language + ext
        shutil.copyfile(self.args.document, translated_copy)
        self.open_document(translated_copy)


        def inject_translations(tm, element):
            if isinstance(element, TextContainer):
                # add text to element
                key = element.item.text()
                if tm.has_key(key):
                    element.item.text.text.set(tm[key])
                
        for canvas in self.doc.canvases():
            c = Canvas(canvas)
            c.walk(partial(inject_translations, tm))

        self.og.windows.first().close()

    def read_translation_memory(self, filename):

        tm = {}
        po = polib.pofile(filename)
        for entry in po.translated_entries():
            if not entry.obsolete:
                tm[entry.msgid] = entry.msgstr

        return tm


    @staticmethod
    def get_parser():
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@',
                                         description="Translate canvases in OmniGraffle 6.",
                                         epilog="If a file fails, simply try again.")

        subparsers = parser.add_subparsers()
        OmniGraffleSandboxedTranslator.add_parser_extract(subparsers)
        OmniGraffleSandboxedTranslator.add_parser_translate(subparsers)



        parser.add_argument('--verbose', '-v', action='count')

        return parser

    @staticmethod
    def add_parser_extract(subparsers):
        sp = subparsers.add_parser('extract',
                                   help="Extract a POT file from an Omnigraffle document.")
        sp.add_argument('source', type=str,
                            help='an OmniGraffle file')
        sp.add_argument('--canvas', type=str,
                            help='translate canvas with given name')
        sp.set_defaults(func=OmniGraffleSandboxedTranslator.cmd_extract_translations)

    @staticmethod
    def add_parser_translate(subparsers):
        sp = subparsers.add_parser('translate',
                                   help="Translate an Omnigraffle document with strings from a po file.")
        sp.add_argument('document', type=str,
                            help='an OmniGraffle file')
        sp.add_argument('language', type=str,
                            help='two-digit language identifier')
        sp.add_argument('po_file', type=str,
                            help='name of po-file')
        sp.add_argument('--canvas', type=str,
                            help='translate canvas with given name')
        sp.set_defaults(func=OmniGraffleSandboxedTranslator.cmd_translate)


def main():
    translator = OmniGraffleSandboxedTranslator()
    translator.args.func(translator)


if __name__ == '__main__':
    main()
