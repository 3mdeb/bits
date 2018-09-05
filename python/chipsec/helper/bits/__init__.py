##
## CHIPSEC: Platform Security Assessment Framework
##
## Copyright (C) 2018 3mdeb Embedded Systems Consulting
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; version 2 of the License.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##


##################################################################################
#
# List of all extension modules: add your module name here
#
##################################################################################

import sys
if sys.platform.startswith('BITS'):
    __all__ = [ "bitshelper" ]
else:
    __all__ = [ ]
