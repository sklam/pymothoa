# Copyright (c) 2012, Siu Kwan Lam
# All rights reserved.
#
# A simple swig interface writer from the header files with special constructs.
# Better to reduce amount of mistake.

import sys, re
line_marker_regex = re.compile(r'//!swig-(.*)')
multiline_begin_prefix = '/*!swig-begin'
multiline_end_prefix = '!swig-end*/'

class SwigPrinter:
    def __init__(self, ostream):
        self.exporting = False
        self.multiline = False
        self.ostream = ostream

    def process(self, line):
        if not self.multiline:
            m = line_marker_regex.match(line)
            if m:
                token = m.groups()[0].strip()
                self.token(token)
                return

            if line.startswith(multiline_begin_prefix):
                self.multiline = True
                return

            if self.exporting:
                print>>self.ostream, line,
        else:
            if line.startswith(multiline_end_prefix):
                self.multiline = False
                return

            print>>self.ostream, line,

    def token(self, token):
        fn = getattr(self, 'do_%s'%token)
        return fn()

    def do_begin(self):
        self.exporting = True

    def do_end(self):
        self.exporting = False

def main(infile, outfile):
    with open(outfile, 'w') as fout:
        swigprinter = SwigPrinter(fout)
        with open(infile) as fin:
            for line in fin:
                swigprinter.process(line)

if __name__ == '__main__':
    try:
        infile, outfile = sys.argv[1], sys.argv[2]
    except IndexError:
        print 'Usage: %s <input> <ouput>' % sys.argv[0]
        print
        print '<input>     C++ header'
        print '<output>    Swig interface'
        print
        sys.exit(1)
    main(infile, outfile)
