import struct
import sys
from datetime import datetime
from pprint import pprint

class UnsupportedFormatException(Exception):
  pass

class Parser:
  def __init__(self, filename):
    self._f = open(filename, 'rb')

  def close(self):
    self._f.close()

  def parse(self):
    self._parse_header()
    self._parse_directories()
    self._parse_directory_entries()

  def _parse_header(self):
    version = self._read(6)
    if version != '\x27\x06\xA4\xD0\x03\x00':
      raise UnsupportedFormatException('Unsupported format: %s. Only the format used by Cathy '
      'v2.15.2 are supported.' % self._hex_repr(version))

    self._properties = {
      'cathy_version': version,
      'vol_date': self._unpack_datetime(),
      'path': self._unpack_str(),
      'vol_name': self._unpack_str(),
      'recorded_name': self._unpack_str(),
      'serial': self._format_serial(self._read(4)),
      'free_space': self._unpack_uint()
    }
    pprint(self._properties)

  def _parse_directories(self):
    self._dirs = []
    num_dirs = self._unpack_uint()
    for i in range(num_dirs):
      self._dirs.append({
        'name':      self._unpack_str(),
        'num_files': self._unpack_uint(),
        'unknown':   self._unpack_uint(),
        'filesize':  self._unpack_uint()
      })
      pprint(self._dirs)

  def _parse_directory_entries(self):
    self._dir_entries = []
    num_entries = self._unpack_uint()
    for i in range(num_entries):
      self._dir_entries.append({
        'date': self._unpack_datetime(),
        'size':       self._unpack_uint(),
        'parent':     self._unpack_ushort(),
        'name':       self._unpack_str()
      })
      pprint(self._dir_entries)

  def _read(self, length):
    return self._f.read(length)

  def _unpack(self, length, fmt_str):
    return self._unpack_multiple(length, fmt_str)[0]

  def _unpack_multiple(self, length, fmt_str):
    return struct.unpack(fmt_str, self._read(length))

  def _unpack_str(self):
    length = self._unpack(1, 'B')
    return self._unpack(length, '%ds' % length)

  def _unpack_datetime(self):
    return datetime.fromtimestamp(self._unpack_uint())

  def _unpack_uint(self):
    return self._unpack(4, 'I')

  def _unpack_ushort(self):
    return self._unpack(2, 'H')

  def _format_serial(self, packed_serial):
    serial = packed_serial[::-1] # Serial stored in reversed format
    serial = self._hex_repr(serial, ' ')
    return '%s-%s' % (serial[0:4], serial[4:8])

  def _hex_repr(self, s, sepr=' '):
    return sepr.join(map(lambda a: '%.2X' % ord(a), s))

def main():
  for filename in sys.argv[1:]:
    Parser(filename).parse()

if __name__ == '__main__':
  main()
