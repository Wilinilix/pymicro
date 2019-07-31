# To maximize python3/python2 compatibility
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

from .StarFile import StarBlock,StarFile,StarList,StarDict
from io import StringIO
# An alternative specification for the Cif Parser, based on Yapps2
# by Amit Patel (http://theory.stanford.edu/~amitp/Yapps)
#
# helper code: we define our match tokens
lastval = ''
def monitor(location,value):
    global lastval
    #print 'At %s: %s' % (location,repr(value))
    lastval = repr(value)
    return value

# Strip extras gets rid of leading and trailing whitespace, and
# semicolons.
def stripextras(value):
     from .StarFile import remove_line_folding, remove_line_prefix
     # we get rid of semicolons and leading/trailing terminators etc.
     import re
     jj = re.compile("[\n\r\f \t\v]*")
     semis = re.compile("[\n\r\f \t\v]*[\n\r\f]\n*;")
     cut = semis.match(value)
     if cut:        #we have a semicolon-delimited string
          nv = value[cut.end():len(value)-2]
          try:
             if nv[-1]=='\r': nv = nv[:-1]
          except IndexError:    #empty data value
             pass
          # apply protocols
          nv = remove_line_prefix(nv)
          nv = remove_line_folding(nv)
          return nv
     else:
          cut = jj.match(value)
          if cut:
               return stripstring(value[cut.end():])
          return value

# helper function to get rid of inverted commas etc.

def stripstring(value):
     if value:
         if value[0]== '\'' and value[-1]=='\'':
           return value[1:-1]
         if value[0]=='"' and value[-1]=='"':
           return value[1:-1]
     return value

# helper function to get rid of triple quotes
def striptriple(value):
    if value:
        if value[:3] == '"""' and value[-3:] == '"""':
            return value[3:-3]
        if value[:3] == "'''" and value[-3:] == "'''":
            return value[3:-3]
    return value

# helper function to populate a StarBlock given a list of names
# and values .
#
# Note that there may be an empty list at the very end of our itemlists,
# so we remove that if necessary.
#

def makeloop(target_block,loopdata):
    loop_seq,itemlists = loopdata
    if itemlists[-1] == []: itemlists.pop(-1)
    # print('Making loop with %s' % repr(itemlists))
    step_size = len(loop_seq)
    for col_no in range(step_size):
       target_block.AddItem(loop_seq[col_no], itemlists[col_no::step_size],precheck=True)
    # now construct the loop
    try:
        target_block.CreateLoop(loop_seq)  #will raise ValueError on problem
    except ValueError:
        error_string =  'Incorrect number of loop values for loop containing %s' % repr(loop_seq)
        print(error_string, file=sys.stderr)
        raise ValueError(error_string)

# return an object with the appropriate amount of nesting
def make_empty(nestlevel):
    gd = []
    for i in range(1,nestlevel):
        gd = [gd]
    return gd

# this function updates a dictionary first checking for name collisions,
# which imply that the CIF is invalid.  We need case insensitivity for
# names.

# Unfortunately we cannot check loop item contents against non-loop contents
# in a non-messy way during parsing, as we may not have easy access to previous
# key value pairs in the context of our call (unlike our built-in access to all
# previous loops).
# For this reason, we don't waste time checking looped items against non-looped
# names during parsing of a data block.  This would only match a subset of the
# final items.   We do check against ordinary items, however.
#
# Note the following situations:
# (1) new_dict is empty -> we have just added a loop; do no checking
# (2) new_dict is not empty -> we have some new key-value pairs
#
def cif_update(old_dict,new_dict,loops):
    old_keys = map(lambda a:a.lower(),old_dict.keys())
    if new_dict != {}:    # otherwise we have a new loop
        #print 'Comparing %s to %s' % (repr(old_keys),repr(new_dict.keys()))
        for new_key in new_dict.keys():
            if new_key.lower() in old_keys:
                raise CifError("Duplicate dataname or blockname %s in input file" % new_key)
            old_dict[new_key] = new_dict[new_key]
#
# this takes two lines, so we couldn't fit it into a one line execution statement...
def order_update(order_array,new_name):
    order_array.append(new_name)
    return new_name

# and finally...turn a sequence into a python dict (thanks to Stackoverflow)
def pairwise(iterable):
    try:
        it = iter(iterable)
        while 1:
            yield next(it), next(it)
    except StopIteration:
        return

# Begin -- grammar generated by Yapps
import sys, re
from . import yapps3_compiled_rt as yappsrt

class StarParserScanner(yappsrt.Scanner):
    def __init__(self, *args,**kwargs):
        patterns = [
         ('([ \t\n\r](?!;))|[ \t]', '([ \t\n\r](?!;))|[ \t]'),
         ('(#.*[\n\r](?!;))|(#.*)', '(#.*[\n\r](?!;))|(#.*)'),
         ('LBLOCK', '(L|l)(O|o)(O|o)(P|p)_'),
         ('GLOBAL', '(G|g)(L|l)(O|o)(B|b)(A|a)(L|l)_'),
         ('STOP', '(S|s)(T|t)(O|o)(P|p)_'),
         ('save_heading', '(S|s)(A|a)(V|v)(E|e)_[][!%&\\(\\)*+,./:<=>?@0-9A-Za-z\\\\^`{}\\|~"#$\';_-]+'),
         ('save_end', '(S|s)(A|a)(V|v)(E|e)_'),
         ('data_name', '_[][!%&\\(\\)*+,./:<=>?@0-9A-Za-z\\\\^`{}\\|~"#$\';_-]+'),
         ('data_heading', '(D|d)(A|a)(T|t)(A|a)_[][!%&\\(\\)*+,./:<=>?@0-9A-Za-z\\\\^`{}\\|~"#$\';_-]+'),
         ('start_sc_line', '(\n|\r\n);([^\n\r])*(\r\n|\r|\n)+'),
         ('sc_line_of_text', '[^;\r\n]([^\r\n])*(\r\n|\r|\n)+'),
         ('end_sc_line', ';'),
         ('data_value_1', '((?!(((S|s)(A|a)(V|v)(E|e)_[^\\s]*)|((G|g)(L|l)(O|o)(B|b)(A|a)(L|l)_[^\\s]*)|((S|s)(T|t)(O|o)(P|p)_[^\\s]*)|((D|d)(A|a)(T|t)(A|a)_[^\\s]*)))[^\\s"#$\'_\\{\\[\\]][^\\s]*)|\'((\'(?=\\S))|([^\n\r\x0c\']))*\'+|"(("(?=\\S))|([^\n\r"]))*"+'),
         ('END', '$'),
        ]
        yappsrt.Scanner.__init__(self,patterns,['([ \t\n\r](?!;))|[ \t]', '(#.*[\n\r](?!;))|(#.*)'],*args,**kwargs)

class StarParser(yappsrt.Parser):
    Context = yappsrt.Context
    def input(self, prepared, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'input', [prepared])
        _token = self._peek('END', 'data_heading')
        if _token == 'data_heading':
            dblock = self.dblock(prepared, _context)
            allblocks = prepared;allblocks.merge_fast(dblock)
            while self._peek('END', 'data_heading') == 'data_heading':
                dblock = self.dblock(prepared, _context)
                allblocks.merge_fast(dblock)
            if self._peek() not in ['END', 'data_heading']:
                raise yappsrt.YappsSyntaxError(charpos=self._scanner.get_prev_char_pos(), context=_context, msg='Need one of ' + ', '.join(['END', 'data_heading']))
            END = self._scan('END')
        else: # == 'END'
            END = self._scan('END')
            allblocks = prepared
        allblocks.unlock();return allblocks

    def dblock(self, prepared, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'dblock', [prepared])
        data_heading = self._scan('data_heading')
        heading = data_heading[5:];thisbc=StarFile(characterset='unicode',standard=prepared.standard);newname = thisbc.NewBlock(heading,prepared.blocktype(overwrite=False));act_block=thisbc[newname]
        while self._peek('save_heading', 'LBLOCK', 'data_name', 'save_end', 'END', 'data_heading') in ['save_heading', 'LBLOCK', 'data_name']:
            _token = self._peek('save_heading', 'LBLOCK', 'data_name')
            if _token != 'save_heading':
                dataseq = self.dataseq(thisbc[heading], _context)
            else: # == 'save_heading'
                save_frame = self.save_frame(prepared, _context)
                thisbc.merge_fast(save_frame,parent=act_block)
        if self._peek() not in ['save_heading', 'LBLOCK', 'data_name', 'save_end', 'END', 'data_heading']:
            raise yappsrt.YappsSyntaxError(charpos=self._scanner.get_prev_char_pos(), context=_context, msg='Need one of ' + ', '.join(['save_heading', 'LBLOCK', 'data_name', 'save_end', 'END', 'data_heading']))
        thisbc[heading].setmaxnamelength(thisbc[heading].maxnamelength);return (monitor('dblock',thisbc))

    def dataseq(self, starblock, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'dataseq', [starblock])
        data = self.data(starblock, _context)
        while self._peek('LBLOCK', 'data_name', 'save_heading', 'save_end', 'END', 'data_heading') in ['LBLOCK', 'data_name']:
            data = self.data(starblock, _context)
        if self._peek() not in ['LBLOCK', 'data_name', 'save_heading', 'save_end', 'END', 'data_heading']:
            raise yappsrt.YappsSyntaxError(charpos=self._scanner.get_prev_char_pos(), context=_context, msg='Need one of ' + ', '.join(['LBLOCK', 'data_name', 'save_heading', 'save_end', 'END', 'data_heading']))

    def data(self, currentblock, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'data', [currentblock])
        _token = self._peek('LBLOCK', 'data_name')
        if _token == 'LBLOCK':
            top_loop = self.top_loop(_context)
            makeloop(currentblock,top_loop)
        else: # == 'data_name'
            datakvpair = self.datakvpair(_context)
            currentblock.AddItem(datakvpair[0],datakvpair[1],precheck=True)

    def datakvpair(self, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'datakvpair', [])
        data_name = self._scan('data_name')
        data_value = self.data_value(_context)
        return [data_name,data_value]

    def data_value(self, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'data_value', [])
        _token = self._peek('data_value_1', 'start_sc_line')
        if _token == 'data_value_1':
            data_value_1 = self._scan('data_value_1')
            thisval = stripstring(data_value_1)
        else: # == 'start_sc_line'
            sc_lines_of_text = self.sc_lines_of_text(_context)
            thisval = stripextras(sc_lines_of_text)
        return monitor('data_value',thisval)

    def sc_lines_of_text(self, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'sc_lines_of_text', [])
        start_sc_line = self._scan('start_sc_line')
        lines = StringIO();lines.write(start_sc_line)
        while self._peek('end_sc_line', 'sc_line_of_text') == 'sc_line_of_text':
            sc_line_of_text = self._scan('sc_line_of_text')
            lines.write(sc_line_of_text)
        if self._peek() not in ['end_sc_line', 'sc_line_of_text']:
            raise yappsrt.YappsSyntaxError(charpos=self._scanner.get_prev_char_pos(), context=_context, msg='Need one of ' + ', '.join(['sc_line_of_text', 'end_sc_line']))
        end_sc_line = self._scan('end_sc_line')
        lines.write(end_sc_line);return monitor('sc_line_of_text',lines.getvalue())

    def top_loop(self, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'top_loop', [])
        LBLOCK = self._scan('LBLOCK')
        loopfield = self.loopfield(_context)
        loopvalues = self.loopvalues(_context)
        return loopfield,loopvalues

    def loopfield(self, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'loopfield', [])
        toploop=[]
        while self._peek('data_name', 'data_value_1', 'start_sc_line') == 'data_name':
            data_name = self._scan('data_name')
            toploop.append(data_name)
        if self._peek() not in ['data_name', 'data_value_1', 'start_sc_line']:
            raise yappsrt.YappsSyntaxError(charpos=self._scanner.get_prev_char_pos(), context=_context, msg='Need one of ' + ', '.join(['data_name', 'data_value_1', 'start_sc_line']))
        return toploop

    def loopvalues(self, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'loopvalues', [])
        data_value = self.data_value(_context)
        dataloop=[data_value]
        while self._peek('data_value_1', 'start_sc_line', 'LBLOCK', 'data_name', 'save_heading', 'save_end', 'END', 'data_heading') in ['data_value_1', 'start_sc_line']:
            data_value = self.data_value(_context)
            dataloop.append(monitor('loopval',data_value))
        if self._peek() not in ['data_value_1', 'start_sc_line', 'LBLOCK', 'data_name', 'save_heading', 'save_end', 'END', 'data_heading']:
            raise yappsrt.YappsSyntaxError(charpos=self._scanner.get_prev_char_pos(), context=_context, msg='Need one of ' + ', '.join(['data_value_1', 'start_sc_line', 'LBLOCK', 'data_name', 'save_heading', 'save_end', 'END', 'data_heading']))
        return dataloop

    def save_frame(self, prepared, _parent=None):
        _context = self.Context(_parent, self._scanner, self._pos, 'save_frame', [prepared])
        save_heading = self._scan('save_heading')
        savehead = save_heading[5:];savebc = StarFile();newname=savebc.NewBlock(savehead,prepared.blocktype(overwrite=False));act_block=savebc[newname]
        while self._peek('save_end', 'save_heading', 'LBLOCK', 'data_name', 'END', 'data_heading') in ['save_heading', 'LBLOCK', 'data_name']:
            _token = self._peek('save_heading', 'LBLOCK', 'data_name')
            if _token != 'save_heading':
                dataseq = self.dataseq(savebc[savehead], _context)
            else: # == 'save_heading'
                save_frame = self.save_frame(prepared, _context)
                savebc.merge_fast(save_frame,parent=act_block)
        if self._peek() not in ['save_end', 'save_heading', 'LBLOCK', 'data_name', 'END', 'data_heading']:
            raise yappsrt.YappsSyntaxError(charpos=self._scanner.get_prev_char_pos(), context=_context, msg='Need one of ' + ', '.join(['save_end', 'save_heading', 'LBLOCK', 'data_name', 'END', 'data_heading']))
        save_end = self._scan('save_end')
        return monitor('save_frame',savebc)


def parse(rule, text):
    P = StarParser(StarParserScanner(text))
    return yappsrt.wrap_error_reporter(P, rule)

# End -- grammar generated by Yapps


