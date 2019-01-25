# pahole command for gdb

# Copyright (C) 2008 Free Software Foundation, Inc.

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import gdb
import gdb.types

class Pahole (gdb.Command):
    """Show the holes in a structure.
This command takes a single argument, a type name.
It prints the type and displays comments showing where holes are."""

    def __init__ (self):
        super (Pahole, self).__init__ ("pahole", gdb.COMMAND_DATA,
                                       gdb.COMPLETE_SYMBOL)

    def pahole (self, atype, level, name, cacheLines):
        if name is None:
            name = ''
        tag = atype.tag
        if tag is None:
            tag = ''
        kind = 'struct' if atype.code == gdb.TYPE_CODE_STRUCT else 'union'
        print ('/* %4d     */ %s%s %s {' % (atype.sizeof, ' ' * (2 * level), kind, tag))
        endpos = 0
        for field in atype.fields():
            # Skip static fields
            if not hasattr (field, ('bitpos')):
                continue
            # find the type
            ftype = field.type.strip_typedefs()

            # Detect hole
            if endpos < field.bitpos:
                hole = field.bitpos - endpos
                print ('/* XXX %d bit hole, try to pack */' % hole)

            # Are we a bitfield?
            if field.bitsize > 0:
                fieldsize = field.bitsize
            else:
                if (ftype.code == gdb.TYPE_CODE_STRUCT or ftype.code == gdb.TYPE_CODE_UNION) and len(ftype.fields()) == 0:
                    fieldsize = 0 # empty struct
                else:
                    fieldsize = 8 * ftype.sizeof # will get packing wrong for structs
        
            print ('/* %3d %4d */' % (field.bitpos // 8, fieldsize // 8), end="")

            endpos = field.bitpos + fieldsize

            print (' ' * (4 + 2 * level), end="")
            print ('%s %s' % (str (ftype), field.name))

            if (cacheLines):
                t = False   
                i = fieldsize//8

                while (((field.bitpos//8) // 64) != (((field.bitpos // 8) + (i)) // 64)):
                    t = True
                    print ("========================")
                    if (i != 64):
                        print ('/* %3d %4d */' % (((field.bitpos // 8 + (fieldsize//8 - i)) // 64 + 1) * 64, fieldsize // 8), end="")
                        print (' ' * (4 + 2 * level), end="")
                        print ('%s %s' % (str (ftype), field.name))
                    i-=64

        print (' ' * (14 + 2 * level), end="")
        print ('} %s' % name)

    def invoke (self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        ptype = None
        cacheLines = False
        for arg in argv:
            if (arg[0] == '-'):
                if (arg == '-c'):
                    cacheLines = True
                else:
                    raise gdb.GdbError('Invalid arg ' + arg)
            else:
                stype = gdb.lookup_type (arg)
                ptype = stype.strip_typedefs()
                if ptype.code != gdb.TYPE_CODE_STRUCT and ptype.code != gdb.TYPE_CODE_UNION:
                    raise gdb.GdbError('%s is not a struct/union type: %s' % (arg, ptype.code))
        if (ptype is None):
            raise gdb.GdbError('no type specified')
        if (cacheLines):
            print ("Cacahelines are printed every 64 bits and are a guidance only that are subject to natural alignment of the object.")
        self.pahole (ptype, 0, '', cacheLines)

Pahole()
