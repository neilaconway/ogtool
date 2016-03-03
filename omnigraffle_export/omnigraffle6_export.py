#!/usr/bin/env python

import argparse
import logging
import os
import shutil
import sys
import tempfile

import appscript

EXPORT_FORMATS = {
        "eps": "EPS",
        "pdf": "PDF",
        "png": "PNG",

        # FIXME
        # "svg": "SVG",
        # "tiff" : "TIFF",
        # "gif" : "GIF",
        # "jpeg" : "JPEG",
    }

SANDBOXED_DIR_6 = '~/Library/Containers/com.omnigroup.OmniGraffle6/Data/'


def export(args):

    og = appscript.app('OmniGraffle')
    og.activate()


    doc = og.open(os.path.abspath(args.source))

    if not doc:
        # fix for inaccessible files
        import subprocess
        subprocess.call(['open',os.path.abspath(args.source)])
        doc = og.open(os.path.abspath(args.source))

    target = os.path.abspath(args.target)

    # TODO: test all those!!!
    og.current_export_settings.draws_background.set(True)
    if args.border:
        og.current_export_settings.include_border.set(True)
        og.current_export_settings.border_amount.set(args.border)
    if args.resolution:
        og.current_export_settings.resolution.set(args.border)
    if args.scale:
        og.current_export_settings.export_scale.set(args.border)

    if args.canvas:
        # TODO test and fix
        og.current_export_settings.area_type.set(appscript.k.current_canvas)
        export_canvas(og, args)
    else:
        og.current_export_settings.area_type.set(appscript.k.entire_document)

        export_item(og, doc, target, args.format)

    og.windows.first().close()

def export_canvas(og, doc, target, args):
    # TODO: this is totally untested
    for canvas in doc.canvases():
        og.windows.first().canvas.set(canvas)
        og.current_export_settings.area_type.set(appscript.k.current_canvas)
        
        og.windows.first().canvas.set(canvas)
        format = 'eps'
        export_format = EXPORT_FORMATS[format]

        fname = '/Users/beb/dev/omnigraffle-export/omnigraffle_export/tmp/%s.%s' % (canvas.name(), format)

        export_item(og, fname, export_format)


def export_item(og, doc, fname, export_format):
    """Export an item."""
 
    # Is OmniGraffle sandboxed?
    # real check using '/usr/bin/codesign --display --entitlements - /Applications/OmniGraffle.app'
    sandboxed = og.version()[0] == '6' and os.path.exists(os.path.expanduser(SANDBOXED_DIR_6))

    export_path = fname

    export_path_with_format = '%s.%s' % (export_path, export_format.lower())
    if sandboxed:
        export_path = os.path.expanduser(SANDBOXED_DIR_6) + os.path.basename(fname)

        # when telling OmniGraffle to export to x, in some cases it exports to x.format -- weird
        export_path_with_format = '%s.%s' % (export_path, export_format.lower())
        # TODO: unlink in case of file when exporting  individual canvas
        if os.path.exists(export_path):
            shutil.rmtree(export_path)
        if os.path.exists(export_path_with_format):
            shutil.rmtree(export_path_with_format)
        logging.debug('OmniGraffle is sandboxed - exporting to: %s' % export_path)


    doc.save(as_=export_format, in_=export_path)
    
    if sandboxed:
        if os.path.exists(fname):
            shutil.rmtree(fname)        
        if os.path.exists(export_path):
            os.rename(export_path, fname)
        else:
            os.rename(export_path_with_format, fname)    
        logging.debug('OmniGraffle is sandboxed - moving %s to: %s' % (export_path, fname))


def main():

    parser = argparse.ArgumentParser(description='Export canvases from OmniGraffle6. If a file fails, simply try again.')
    
    # TODO test and add formats
    parser.add_argument('format', type=str,
                    help='Export format: EPS,...')
    
    parser.add_argument('source', type=str,
                    help='an OmniGraffle file')
    parser.add_argument('target', type=str,
                    help='folder to export to')
    # TODO: implement 
    parser.add_argument('--canvas', type=str,
                        help='export canvas with given name')
    # TODO: implement
    parser.add_argument('--scale', type=float,
                        help=' The scale to use during export')
    # TODO: implement
    parser.add_argument('--resolution', type=float,
                        help='The number of pixels per point in the resulting exported image (1.0 for 72 DPI).')

    # TODO: implement
    parser.add_argument('--transparent', dest='transparent', action='store_true',
                        help='export with transparent background')

    # TODO: implement
    parser.add_argument('--border', type=int,
                        help='The number of pixels of border area to include in exported graphics.')

    args = parser.parse_args()

    print 'exporting', args.source
    export(args)    


if __name__ == '__main__':
    main()

