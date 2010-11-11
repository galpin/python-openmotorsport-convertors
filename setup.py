from distutils.core import setup

setup(
  name='python-openmotorsport-convertors',
  version='0.1',
  description='A library of convertors from various file formats to OpenMotorsport.',
  author='Martin Galpin',
  author_email='m@66laps.com',
  url='http://developer.66laps.com/',
  license='GNU General Public License v3',
  packages=['piresearch'],
  scripts=['lfs2om.py', 'imp2om.py'],
  py_modules=['lfs2om'],
  # disable install requires until packages are in PyPi
  #install_requires=['python-liveforspeed', 'python-openmotorsport', 'numpy']
)