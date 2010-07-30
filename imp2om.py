#!/usr/bin/env python2.6
#
# Converts a given LFS Replay Analayser file to OpenMotorsport.
#
# Author: Martin Galpin (m@66laps.com)
#
# Copyright (C) 2010 66laps Limited. All rights reserved.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301,
# USA.

__author__  = 'Martin Galpin'
__contact__ = 'm@66laps.com'
__version__ = '0.1'
__license__ = 'GNU General Public License v3'

import os, sys
import numpy as np
from piresearch import IMP
import openmotorsport.openmotorsport as OM

def convert(source_folder):
  '''Creates a new OpenMotorsport file from a given Pi IMP folder. Returns
  the path to the new file.'''
  source = IMP.Session(source_folder)
    
  dest = OM.Session()
  dest.metadata.user = source.driver
  dest.metadata.venue['name'] = source.track
  dest.metadata.vehicle['name'] = 'Unknown' # not stored
  dest.metadata.comments = 'Converted from Pi IMP using imp2om.py'
  convert_laps_to_markers(source.laps, dest)
  dest.num_sectors = 0
    
  [dest.add_channel(convert_channel(c)) for c in source.channels]

  return dest.write('output.om')
  
def convert_laps_to_markers(laps, dest):
  '''Convert a list of individual lap times into a list of markers over the
  duratino on the session.'''
  cumulative = 0
  for lap in laps:
    cumulative += lap
    dest.add_marker(cumulative)

def convert_channel(imp_channel):
  '''Straight conversion from IMP.Channel to OM.Channel.'''
  return OM.Channel(
    id = imp_channel.id,
    name = imp_channel.name,
    units = imp_channel.units, # TODO normalize
    interval = imp_channel.sample_rate,
    data = imp_channel.data
  )

# main function
if __name__ == "__main__":
  if len(sys.argv) < 2:
    print >> sys.stderr, 'Converts an IMP folder export from Pi Version 6 to OpenMotorsport.'
    print >> sys.stderr, 'usage: python imp2om.py source_folder'
    sys.exit(0)
    
  print 'Successfully created', convert(sys.argv[-1])