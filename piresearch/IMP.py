#!/usr/bin/python2.6
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
'''
A library that provdes a python interface to the IMP format exported from
Pi Analysis V6.

For the record, I don't actually know what the IMP format is or who created
it. However, I do know that I needed to extract data and that there was value
in reverse engineering it.  If you do know, please feel free to e-mail me.
'''

__author__  = 'Martin Galpin'
__contact__ = 'm@66laps.com'
__version__ = '0.1'
__license__ = 'GNU General Public License v3'

import struct
import numpy
import re
import StringIO
    
class Session(object):
  '''This class represents the data contained in a IMP folder that has
  been exported from Pi Analysis V6.
  
  Usage:
  
    from piresearch import imp
    session = imp.Session('.')
    print session.laps
    print session.channels
    
  '''
  def __init__(self, root=None):
    self.channels = None
    self.laps = []
    self.driver = None
    self.track = None
    
    if root:
      self.fromfile(root)

  def fromfile(self, root):
    '''Read an IMP folder from the given root path. The folder must contain
    at minimum a 'info.dat', 'desc.dat', 'laps.dat' and 'xxx.dat' binary file 
    for each channel defined in 'info.dat''.'''
    self.channels = self._read_info(root)
    self._read_channels(self.channels, root)
    self.laps = self._read_laps(root)
    self.track, self.driver = self._read_desc(root)
    return self
       
  def _read_info(self, root, filename='info.dat'):
    '''
    Reads the 'info.dat' file and parses out channel names and unit abbreviations.
  
    The format of the 'info.dat' files appear to be:
  
    num     unit      offset    description
    ---     ----      ------    -----------
    HEADER BLOCK
    2       byte      0         number of channels (x)
    x       channel   2         a channel block for each channel (see below)       
    CHANNEL BLOCK
    10      char      0         name of channel (delimeted by \x00)
    6       byte      10        unidentified
    6       char      16        abbreivation of units (delimeted by \x00)
    12      byte      24        unidentified
    EOF
    '''
    channels = []
    with open('%s/%s' % (root, filename), 'rb') as f:
      # file header contains number of channels
      buf = f.read(2)
      num_channels = struct.unpack('h', buf)[0]
  
      for i in range(0, num_channels):
        channel = Channel(id=i)
        # channel name
        channel.name = _readchars(f, 10).strip()
        # unidentified
        f.read(6)
        # channel units
        channel.units = _readchars(f, 6).strip()
        # unidentified
        f.read(12)
        channels.append(channel)
      
    return channels

  def _read_channels(self, channels, root):
    '''
    Reads the 'xxx.dat' data files and extracts sampled data.

    The data is stored as 32-bit single precision floats (IEE-754).

    Arguments:
      channels
        A list of channels to read.
      path
        The root path of the IMP archive.
    '''
    for channel in channels: 
      with open('%s/%03d.dat' % (root, channel.id), 'rb') as f:
        f.seek(4) # unidentified 4-bytes
        buf = f.read(4)
        interval = struct.unpack('<I', buf)[-1]
      
        # HELP: i don't know why the sample interval is x10.
        # so 1Hz = 10000, 2Hz = 5000 and 10Hz = 1000. does anybody else?
        channel.sample_interval = interval / 10

        f.seek(20) # data starts are byte-20
        data = []
        while True:
          buf = f.read(4)
          if buf == '': break #EOF
          data.append(struct.unpack('<f', buf)[-1])     
        channel.data = numpy.array(data, numpy.float32)
      
  def _read_laps(self, root, filename='lap.dat'):
    '''Reads the 'laps.dat' file to get the lap times.'''
    times = []
    with open('%s/%s' % (root, filename), 'r') as f:
      for line in f.xreadlines():
        times.append(_tomilliseconds(line.strip()))
    return times
    
  def _read_desc(self, root, filename='desc.dat'):
    '''Reads the 'desc.dat' file to get the driver and track name.'''
    with open('%s/%s' % (root, filename), 'rb') as f:
      f.seek(8) # unidentified 8-bytes
      track = _readchars(f, 12).strip()
      driver = _readchars(f, 12).strip()
    return track, driver


class Channel(object):
  '''A basic object that represents a channel (including sampled data).'''
  def __init__(self, **kwargs):
    self.id = None
    self.name = None
    self.units = None
    self.data = None
    self.sample_rate = None
    self.__dict__.update(**kwargs)

  def __repr__(self):
    return '%s (%s)' % (self.name, self.units)

def _readchars(source, size, delimeter='\x00'):
  '''Reads size characters from source up until a given size.'''
  destination = StringIO.StringIO()
  while size >= 0:
    c = struct.unpack('<c', source.read(1))[0]
    size -= 1
    if c == delimeter:
      break
    destination.write(_encode(c))
  source.read(size)
  return destination.getvalue()  

def _tomilliseconds(str):
  '''Converts a string formatted as MM:SS:MS to pure seconds.'''
  search = re.search('(\d+):(\d+).(\d+)', str)
  milliseconds = 0.
  if search:
    if search.group(1):
      milliseconds += int(search.group(1)) * 60000
    if search.group(2):
      milliseconds += int(search.group(2)) * 1000
    if search.group(3):
      milliseconds += int(search.group(3)) * 10
  return milliseconds
  
def _encode(c):
  '''Encode troublesome extended ASCII characters to Unicode.'''
  if ord(c) == 176: # degrees symbol
    return 'deg'
  return c