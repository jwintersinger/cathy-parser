from __future__ import division, print_function
import struct
import sys
from datetime import datetime
import xml.etree.ElementTree as ET

class UnsupportedFormatException(Exception):
  pass


def hex_repr(s, sepr=' '):
  return sepr.join(map(lambda a: '%.2X' % ord(a), s))

class CathyParser:
  def __init__(self, filename):
    self._f = open(filename, 'rb')

  def close(self):
    self._f.close()

  def parse(self):
    self._parse_header()
    self._parse_directories()
    self._parse_directory_entries()

  def register_handlers(self, header_handler, directory_handler, dir_entry_handler):
    self._handlers = {
      'header':    header_handler,
      'directory': directory_handler,
      'dir_entry': dir_entry_handler
    }

  def _parse_header(self):
    version = self._read(6)
    if version != b'\x27\x06\xA4\xD0\x03\x00':
      raise UnsupportedFormatException('Unsupported format: %s. Only the format used by Cathy '
      'v2.15.2 are supported.' % hex_repr(version))

    props = {
      'cathy_version': version,
      'vol_date': self._unpack_datetime(),
      'path': self._unpack_str(),
      'vol_name': self._unpack_str(),
      'recorded_name': self._unpack_str(),
      'serial': self._format_serial(self._read(4)),
      'free_space': self._unpack_uint()
    }
    self._handlers['header'](props)

  def _parse_directories(self):
    num_dirs = self._unpack_uint()
    for i in range(num_dirs):
      props = {
        'name':      self._unpack_str(),
        'num_files': self._unpack_uint(),
        'unknown':   self._read(4),
        'filesize':  self._unpack_uint()
      }
      self._handlers['directory'](props)

  def _parse_directory_entries(self):
    num_entries = self._unpack_uint()
    for i in range(num_entries):
      props = {
        'date': self._unpack_datetime(),
        'size':       self._unpack_uint(),
        'parent':     self._unpack_ushort(),
        'name':       self._unpack_str()
      }
      self._handlers['dir_entry'](props)

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
    serial = hex_repr(serial, '')
    return '%s-%s' % (serial[0:4], serial[4:8])



class XmlWriter:
  def __init__(self, filename):
    self._filename = filename
    self._root = ET.Element('volume')
    self._directories = ET.SubElement(self._root, 'directories')
    self._dir_entries = ET.SubElement(self._root, 'dir_entries')

  def write_header(self, props):
    props['cathy_version'] = hex_repr(props['cathy_version'])
    props['vol_date'] = props['vol_date'].isoformat()
    for prop, value in props.items():
      el = ET.SubElement(self._root, prop)
      el.text = unicode(value)

  def write_directory(self, props):
    name = props['name']
    del props['name']

    props['unknown'] = hex_repr(props['unknown'])
    for k in props:
      props[k] = unicode(props[k])

    el = ET.SubElement(self._directories, 'directory', props)
    el.text = name

  def write_dir_entry(self, props):
    name = props['name']
    del props['name']

    props['date'] = props['date'].isoformat()
    for k in props:
      props[k] = unicode(props[k])

    el = ET.SubElement(self._dir_entries, 'dir_entry', props)
    el.text = name

  def write(self):
    self._indent(self._root)
    tree = ET.ElementTree(self._root)
    tree.write(self._filename)

  def close(self):
    self._f.close()

  # Taken from http://effbot.org/zone/element-lib.htm.
  def _indent(self, elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
      if not elem.text or not elem.text.strip():
        elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
          elem.tail = i
        for elem in elem:
          self._indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
          elem.tail = i
    else:
      if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def main():
  for filename in sys.argv[1:]:
    writer = XmlWriter('ding')
    parser = CathyParser(filename)
    parser.register_handlers(
      header_handler    = lambda header: writer.write_header(header),
      directory_handler = lambda directory: writer.write_directory(directory),
      dir_entry_handler = lambda dir_entry: writer.write_dir_entry(dir_entry)
    )
    parser.parse()
    writer.write()

if __name__ == '__main__':
  main()
