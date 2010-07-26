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
import lfs
import openmotorsport.openmotorsport as OM
import numpy as np

# Maps the LFS RAF data block field to a tuple containing an OpenMotorsport
# name and group.
CHANNEL_MAP = {
  'throttle': ('Throttle', 'Driver'),
  'brake': ('Brake', 'Driver'),
  'input_steer': ('Steering', 'Driver'),
  'clutch': ('Clutch', 'Driver'),
  'handbrake': ('Handbrake', 'Driver'),
  'gear': ('Gear', 'Driver'),
  'lateral_g': ('Acceleration X', 'Acceleration'),
  'forward_g': ('Acceleration Y', 'Acceleration'),
  'upwards_g': ('Acceleration Z', 'Acceleration'),
  'speed': ('Speed', 'Position'),
  'car_distance': ('Distance', 'Position'),
  'position_x': ('Position X', 'Position'),
  'position_y': ('Position Y', 'Position'),
  'position_z': ('Position Z', 'Position'),
  'engine_speed': ('Engine Speed', 'Engine'),
  'index_distance': ('Distance (Index)', 'Position'),
  'heading': ('Heading', 'Position')
}

# Map a dynamic wheel block for each wheel to an individual channel and group.
WHEELS = ['Wheel RF', 'Wheel LF', 'Wheel RR', 'Wheel LR']
for group in WHEELS:
  CHANNEL_MAP.update({
    'suspension_deflect': ('Suspension Deflection', group),
    'steer': ('Steer', group),
    'x_force': ('Force X', group),
    'y_force': ('Force Y', group),
    'vertical_load': ('Veritcal Load', group),
    'angular_velocity': ('Angular Velocity', group),
    'lean': ('Lean', group),
    'air_temp': ('Air Temperature', group),
    'slip_fraction': ('Slip Fraction', group),
  })

# A definition of the OpenMotorsport channels and groups.
CHANNELS = [
  {'name':'Throttle', 'units':'%', 'group':'Driver'},
  {'name':'Brake', 'units':'%', 'group':'Driver'},
  {'name':'Clutch', 'units':'%', 'group':'Driver'},
  {'name':'Steering', 'units':'rad', 'group':'Driver'},
  {'name':'Handbrake', 'units':'%', 'group':'Driver'},
  {'name':'Gear', 'units':'gear', 'group':'Driver'},
  {'name':'Engine Speed', 'units':'rad/s', 'group':'Engine'},
  {'name':'Acceleration X', 'units':'g', 'group':'Acceleration'},
  {'name':'Acceleration Y', 'units':'g', 'group':'Acceleration'},
  {'name':'Acceleration Z', 'units':'g', 'group':'Acceleration'},
  {'name':'Speed', 'units':'m/s', 'group':'Position'},
  {'name':'Distance', 'units':'m', 'group':'Position'},
  {'name':'Heading', 'units':'rad', 'group':'Position'},
  {'name':'Distance (Index)', 'units':'m', 'group':'Position'},
  {'name':'Position X', 'units':'m', 'group':'Position'},
  {'name':'Position Y', 'units':'m', 'group':'Position'},
  {'name':'Position Z', 'units':'m', 'group':'Position'}
]

# A set of multiplcation factors to apply to a small number of channels
MULTIPLICATION_FACTORS = {
  # converting 0-1 include a percentage
  'throttle': 100,
  'brake': 100,
  'clutch': 100,
  'handbrake': 100
}

# A definition of channels for each wheel (each with their own group).
for group in WHEELS:
  CHANNELS.extend([
    {'name':'Suspension Deflection', 'units': 'N', 'group': group},
    {'name':'Steer', 'units': 'rad', 'group': group},
    {'name':'Force X', 'units': 'N', 'group': group},
    {'name':'Force Y', 'units': 'N', 'group': group},
    {'name':'Veritcal Load', 'units': 'N', 'group':group},
    {'name':'Angular Velocity', 'units':'rad/s', 'group':group},
    {'name':'Lean', 'units':'rad', 'group':group},
    {'name':'Air Temperature', 'units':'c', 'group':group},
    {'name':'Slip Fraction', 'group':group} # TODO units for 0-255
  ])

def convert_data_block(index, block, session):
  '''Convert an instance of lfs.DataBlock into an openmotorsport.Session.'''
  for k, v in block.__dict__.items():
    try:
      # apply any multiplication factors
      if k in MULTIPLICATION_FACTORS:
        v = v * MULTIPLICATION_FACTORS[k]
        
      session.get_channel(CHANNEL_MAP[k][0], CHANNEL_MAP[k][1]).data[index] = v
    except: pass # field not mapped
      
  # TODO what is the order of the wheel blocks?
  for x, group in enumerate(WHEELS):
    convert_wheel_data_block(index, block.wheels[x], group, session)      
    
def convert_wheel_data_block(index, block, group, session):
  '''Convert an instance of lfs.DynamicWheelInfo to an openmotorsport.Session.'''
  for k, v in block.__dict__.items():
    session.get_channel(CHANNEL_MAP[k][0], group).data[index] = v
  
def convert(filepath):
  '''Converts a given LFS Replay Analayser file to OpenMotorsport. Returns the
  path to the new file.'''
  replay = lfs.Replay(filepath)

  session = OM.Session()
  session.metadata.user = replay.player
  session.metadata.venue['name'] = replay.track
  session.metadata.venue['configuration'] = replay.config
  session.metadata.vehicle['name'] = replay.car
  session.metadata.datasource = 'Live For Speed %s' % replay.lfs_version
  session.metadata.comments = comments(replay)

  num_blocks = len(replay.data)
        
  session.num_sectors = replay.num_splits - 1
  [session.add_marker(mstos(x)) for x in replay.splits]
  
  for index, c in enumerate(CHANNELS): 
    session.add_channel(OM.Channel(
      id = index,
      interval = replay.update_interval,
      name = c['name'],
      units = c['units'] if 'units' in c else None,
      group = c['group'],
      data = np.zeros(num_blocks, dtype=np.float32)
    ))
    
  [convert_data_block(index, b, session) for index, b in enumerate(replay.data)]
      
  return session.write('%s.om' % os.path.splitext(filepath)[0])
  

def comments(replay): return 'Weather: %s' % (replay.weather)
def mstos(x): return float(x)/1000

# main function
if __name__ == "__main__":
  if len(sys.argv) < 2:
    print >> sys.stderr, 'Converts a given LFS Replay Analayser file to OpenMotorsport.'
    print >> sys.stderr, 'usage: python lfs2om.py source_file'
    sys.exit(0)
    
  print 'Successfully created', convert(sys.argv[-1])