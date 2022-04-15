#!/usr/bin/env python
"""A command line client to duckdb"""

from cmd import Cmd
from pprint import pformat
import datetime

try:
    import readline
except ImportError:
    pass

import duckdb

__version__ = '0.2.3'

###############################################################################

# readable, editable way to define the frame characters:
FRAME_FANCY = "╔═╤═╗" + \
              "║ │ ║" + \
              "╠═╪═╣" + \
              "║ │ ║" + \
              "╟─┼─╢" + \
              "║ │ ║" + \
              "╚═╧═╝" 
FRAME_THIN = "┌─┬─┐" + \
             "│ │ │" + \
             "├─┼─┤" + \
             "│ │ │" + \
             "├─┼─┤" + \
             "│ │ │" + \
             "└─┴─┘" 
FRAME_RAW = "+-+-+" + \
            "| | |" + \
            "+-+-+" + \
            "| | |" + \
            "+-+-+" + \
            "| | |" + \
            "+-+-+" 
# offsets of the relevant, distinguishable frame chars:
# ╔═╤═╗ offsets 0..4
# ║ │ ║ offsets 5..9
# ╠═╪═╣ offsets 10..14
# ║ │ ║ offsets 15..19
# ╟─┼─╢ offsets 20..24
# ║ │ ║ offsets 25..29
# ╚═╧═╝ offsets 30..34
# the corners:
FCO_CORNER_UPPER_LEFT  = 0
FCO_CORNER_UPPER_RIGHT = 4
FCO_CORNER_LOWER_LEFT  = 30
FCO_CORNER_LOWER_RIGHT = 34
# the outer "bars":
FCO_OUTER_BAR_TOP    = 1
FCO_OUTER_BAR_LEFT   = 5
FCO_OUTER_BAR_RIGHT  = 9
FCO_OUTER_BAR_BOTTOM = 31
# the half-junctions: where inner line join the outer frame:
FCO_JUNCTION_TOP        = 2
FCO_JUNCTION_HEAD_LEFT  = 10    # between head and content
FCO_JUNCTION_HEAD_RIGHT = 14    # between head and content
FCO_JUNCTION_LEFT       = 20
FCO_JUNCTION_RIGHT      = 24
FCO_JUNCTION_BOTTOM     = 32
# inner lines:
FCO_HEAD_BAR_HORIZONTAL  = 11  # between head and content
FCO_INNER_BAR_HORIZONTAL = 21
FCO_INNER_BAR_VERTICAL   = 7
# inner junction/cross:
FCO_INNER_JUNCTION_HEAD = 12    # between head and content
FCO_INNER_JUNCTION      = 22

#v22## ###############################################################################
#v22## 
#v22## # readable, editable way to define the frame characters:
#v22## FRAME_FANCY = "┌─┬─┐" + \
#v22##               "│ │ │" + \
#v22##               "├─┼─┤" + \
#v22##               "│ │ │" + \
#v22##               "└─┴─┘" 
#v22## FRAME_FALLBACK = "+-+-+" + \
#v22##                  "| | |" + \
#v22##                  "+-+-+" + \
#v22##                  "| | |" + \
#v22##                  "+-+-+" 
#v22## FRAME_FRAME2 = "╔═╤═╗" + \
#v22##                "║ │ ║" + \
#v22##                "╟─┼─╢" + \
#v22##                "║ │ ║" + \
#v22##                "╚═╧═╝" 
#v22## # offsets of the relevant, distinguishable frame chars:
#v22## # ┌─┬─┐ offsets 0..4
#v22## # │ │ │ offsets 5..9
#v22## # ├─┼─┤ offsets 10..14
#v22## # │ │ │ offsets 15..19
#v22## # └─┴─┘ offsets 20..24
#v22## # the corners:
#v22## FCO_CORNER_UPPER_LEFT  = 0
#v22## FCO_CORNER_UPPER_RIGHT = 4
#v22## FCO_CORNER_LOWER_LEFT  = 20
#v22## FCO_CORNER_LOWER_RIGHT = 24
#v22## # the outer "bars":
#v22## FCO_OUTER_BAR_TOP    = 1
#v22## FCO_OUTER_BAR_LEFT   = 5
#v22## FCO_OUTER_BAR_RIGHT  = 9
#v22## FCO_OUTER_BAR_BOTTOM = 21
#v22## # the half-junctions: where inner line join the outer frame:
#v22## FCO_JUNCTION_TOP    = 2
#v22## FCO_JUNCTION_LEFT   = 10
#v22## FCO_JUNCTION_RIGHT  = 14
#v22## FCO_JUNCTION_BOTTOM = 22
#v22## # inner lines:
#v22## FCO_INNER_BAR_HORIZONTAL = 11
#v22## FCO_INNER_BAR_VERTICAL   = 7
#v22## # inner junction/cross:
#v22## FCO_INNER_JUNCTION = 12
#v22## 
###############################################################################

HTMLHEADER = """
<html>
<head>
    <style>
        *     {  font-family: sans-serif; }
        body  { background-color: silver; }
        thead { background-color: lightblue; }
        table { border-collapse: collapse; }
        td    { border: 1px solid black; }
    </style>
    <title>gadwall/DuckDB output</title>
</head>
<body>
<h1>gadwall/DuckDB output</h1>
"""

HTMLFOOTER_TEMPLATE = """
<hr>
<small>%s</small>
</body>
</html>
"""

###############################################################################
"""
helper function: for a list of strings, replace the beginning 'dot_' by '.'
returns a modified list
"""
def undotlist(strlist):
    output = []
    for string in strlist:
        if string.startswith('dot_'):
            output.append('.'+string[4:])
        else:
            output.append(string)
    return output

###############################################################################
"""
modified Cmd class - to enable commands starting ".", which, concerning the implementation, is treated like "dot_".
e.g. ".html params" will try to call a method do_dot_html(params)
"""

class DotCmd(Cmd):

    def parseline(self, line):
        """Parse the line into a command name and a string containing
        the arguments.  Returns a tuple containing (command, args, line).
        'command' and 'args' may be None if the line couldn't be parsed.
        """
        line = line.strip()
        if not line:
            return None, None, line
        elif line[0] == '?':
            line = 'help ' + line[1:]
        elif line[0] == '!':
            if hasattr(self, 'do_shell'):
                line = 'shell ' + line[1:]
            else:
                return None, None, line
        # next two lines (simply inserted) are the mod from Cmd
        elif line[0] == '.':
            line = 'dot_' + line[1:]
        # (end of mod from Cmd)
        i, n = 0, len(line)
        while i < n and line[i] in self.identchars: i = i+1
        cmd, arg = line[:i], line[i:].strip()
        return cmd, arg, line

    def do_help(self, arg):
        'List available commands with "help" or detailed help with "help cmd".'
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc=getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write("%s\n"%str(doc))
                        return
                except AttributeError:
                    pass
                if arg[0] == '.':
                    try:
                        print('?', 'do_dot_' + arg[1:])
                        doc=getattr(self, 'do_dot_' + arg[1:]).__doc__
                        if doc:
                            self.stdout.write("%s\n"%str(doc))
                            return
                    except AttributeError:
                        pass
                self.stdout.write("%s\n"%str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]]=1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd=name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n"%str(self.doc_leader))
            # next three lines are changed for the mod from Cmd:
            # the sorted(undotlist()) calls were inserted
            self.print_topics(self.doc_header,   sorted(undotlist(cmds_doc)),   15,80)
            self.print_topics(self.misc_header,  sorted(undotlist(list(help.keys()))),15,80)
            self.print_topics(self.undoc_header, sorted(undotlist(cmds_undoc)), 15,80)
            # (end of mod from Cmd)

###############################################################################
# helper function: Replace None by a certain string; leave everything else unchanged:
def nvlstr(val, fallback=''):
    if val == None:
        return fallback
    elif type(val) in (int, str, bool, datetime.datetime):
        return str(val)
    else:
        return pformat(val)

###############################################################################
class Gadwall(DotCmd):
    intro = 'Welcome to the gadwall, a duckdb shell. Type help or ? to list commands.\n'
    prompt = 'duckdb> '
    htmlFile = None
    framecharset = FRAME_FANCY
    framing_name = 'FANCY'

    def __init__(self, file_name):
        super().__init__()
        self.file_name = file_name
        self.conn = duckdb.connect(file_name)

    def do_dot_quit(self, arg):
        """Exit the program"""
        self.conn.close()
        self.closeHTML()
        return True

    def do_EOF(self, arg):
        return self.do_dot_quit(arg)

    def do_dot_db(self, arg):
        """Show current database"""
        print('database: ' + self.file_name)
        self.writeHTML(f'<h2>database: {self.file_name}</h2>\n')

    def do_dot_schema(self, arg):
        """Show database or table schema; special keyword "*" lists it recursively"""
        arg = arg.strip()
        if arg == '*':
            self.default('PRAGMA show_tables;')
            # "recursion":
            self.conn.execute('PRAGMA show_tables;')
            data = self.conn.fetchall()
            if data:
                for line in data:
                    print(f'.schema {line[0]}')
                    self.default(f"PRAGMA table_info('{line[0]}')")
        elif arg:
            self.default(f"PRAGMA table_info('{arg}')")
        else:
            self.default('PRAGMA show_tables;')

    def do_dot_html(self, arg):
        """enable html output to given filename; "off" turns it off; no filename shows the current state"""
        arg = arg.strip()
        if arg == '':
            if self.htmlFile:
                print('current html output:', self.htmlFile.name)
            else:
                print('currently no html output')
        elif arg.lower() == 'off':
            self.closeHTML()
        else:
            self.openHTML(arg)

    def do_dot_frame(self, arg):
        """select the framing (in the terminal): one "raw" (ASCII only), "fancy" (frame chars) and "thin" (like "fancy", but single outlines)"""
        arg = arg.strip()
        charsetname = arg.upper()
        try:
            self.framecharset = globals()['FRAME_'+charsetname]
            self.framing_name = charsetname
        except KeyError:
            if charsetname:
                print('unrecognized .frame choice', arg)
        print('current framing:', self.framing_name)

    def default(self, arg):
        if not arg.strip():
            return

        self.writeHTML('<h2>%s</h2>\n' % arg)
        try:
            self.conn.execute(arg)
        except RuntimeError as err:
            print(f'ERROR: {err}')
            return
        if arg.lower().startswith('explain '):
            for row in self.conn.fetchall():
                print(row[0]+':\n'+row[1])
                self.writeHTML('<h3>%s:</h3><pre style=\'font-family: "Lucida Console", monospace;\'>%s</pre>\n' % row)
        else:
            self.print_tabled()

    def emptyline(self):
        # Override default of repeating last command
        return

    def openHTML(self, filename):
        # open HTML file for dumping results; write "header"
        self.closeHTML()
        self.htmlFile = open(filename, 'w', encoding='UTF-8')
        self.writeHTML(HTMLHEADER)
        print('writing following commands to: "%s"' % filename)

    def writeHTML(self, txt):
        if self.htmlFile:
            self.htmlFile.write(txt)

    def closeHTML(self):
        # open HTML file for dumping results; write "footer"
        if self.htmlFile:
            self.writeHTML(HTMLFOOTER_TEMPLATE % str(datetime.datetime.now()))
            self.htmlFile.close()
            print('html file "%s" closed' % self.htmlFile.name)
            self.htmlFile = None

    def bar(self, col_widths, fco_left, fco_cell, fco_junction, fco_right):
        """ helper function to print_tabled: build a frame line: 
            chars according to self.framecharset; cell "widths" according to col_widths
            fco_left/right: offset to the left/right "border"/juntion,
            fco_cell: ... to the char "within" the cells
            fco_junction: ... to the char "between" the cells
        """
        return self.framecharset[fco_left] + self.framecharset[fco_junction].join(self.framecharset[fco_cell]*col_widths[i] for i in range(len(col_widths))) + self.framecharset[fco_right]

    def print_tabled(self):
        """ print the just queried with headline to console and the HTML file """

        # retrieve the data *once* (it can be a generator!)
        data = self.conn.fetchall()

        align_right = [ self.conn.description[i][1] == 'NUMBER' for i in range(len(self.conn.description)) ]
        if self.htmlFile:
            html_aligns = [ { True:' align="right"', False:'' }[align_right[i]] for i in range(len(self.conn.description)) ]
        if data:
            col_width = [max(len(nvlstr(x, '(NULL)')) for x in col) for col in zip(*data)]
            for col in range(len(self.conn.description)):
                col_width[col] = max(col_width[col], len(self.conn.description[col][0]))
            formats = [ '%'+{ True:'', False:'-' }[align_right[i]]+str(col_width[i])+'s' for i in range(len(self.conn.description)) ]
        else:
            col_width = [ len(self.conn.description[col][0]) for col in range(len(self.conn.description)) ]
            formats = [ '%'+str(col_width[i])+'s' for i in range(len(self.conn.description)) ]
        line_format = self.framecharset[FCO_OUTER_BAR_LEFT] + self.framecharset[FCO_INNER_BAR_VERTICAL].join(formats) + self.framecharset[FCO_OUTER_BAR_RIGHT]
        if self.htmlFile:
            html_line_format = '<tr>' + '\n'.join([ '\t<td %s>%%s</td>' % html_aligns[i] for i in range(len(self.conn.description)) ]) + '\n</tr>\n'
        print(self.bar(col_width, FCO_CORNER_UPPER_LEFT, FCO_OUTER_BAR_TOP, FCO_JUNCTION_TOP, FCO_CORNER_UPPER_RIGHT))
        # columns headers:
        print(line_format % tuple( self.conn.description[i][0] for i in range(len(self.conn.description)) ) )
        if self.htmlFile:
            self.writeHTML('<table><thead><tr>' + \
                            '\n'.join([ '\t<td>%s</td>' % self.conn.description[i][0] for i in range(len(self.conn.description)) ]) + \
                            '\n</tr></thead>\n<tbody>\n')
        if data:
            innerbar = self.bar(col_width, FCO_JUNCTION_HEAD_LEFT, FCO_HEAD_BAR_HORIZONTAL, FCO_INNER_JUNCTION_HEAD, FCO_JUNCTION_HEAD_RIGHT)
            for line in data:
                print(innerbar)
                if innerbar[0] != self.framecharset[FCO_JUNCTION_LEFT]:
                    # head separator line was different from the remaining => switch after the line above the first data row == between head and content
                    innerbar = self.bar(col_width, FCO_JUNCTION_LEFT, FCO_INNER_BAR_HORIZONTAL, FCO_INNER_JUNCTION, FCO_JUNCTION_RIGHT)
                print(line_format % tuple( nvlstr(line[i], '(NULL)') for i in range(len(self.conn.description)) ))
                if self.htmlFile:
                    self.writeHTML('<tr>' + html_line_format % tuple( nvlstr(line[i], '<i>NULL</i>') for i in range(len(self.conn.description)) ) + '\n</tr>\n')
            self.writeHTML('</tbody></table>\n')
        else:
            print('(0 rows)')
            self.writeHTML('</tbody></table>\n<p><i>(0 rows)</i></p>\n')
        print(self.bar(col_width, FCO_CORNER_LOWER_LEFT, FCO_OUTER_BAR_BOTTOM, FCO_JUNCTION_BOTTOM, FCO_CORNER_LOWER_RIGHT))

###############################################################################
def main():
    from argparse import ArgumentParser, FileType

    parser = ArgumentParser(description=__doc__)
    parser.add_argument('filename', type=FileType('r'))
    args = parser.parse_args()

    args.filename.close()
    cmd = Gadwall(args.filename.name)
    try:
        cmd.cmdloop()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
