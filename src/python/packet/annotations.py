#
# Copyright (c) 2012, The Packet project authors. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# The GNU General Public License is contained in the file LICENSE.
#
''' Annotation module. '''

__author__ = 'Soheil Hassas Yeganeh <soheil@cs.toronto.edu>'

__packet_level_annotations = {}  # pylint: disable=C0103
__field_level_annotations = {}  # pylint: disable=C0103

def packet_level_annotation(name):
  ''' Decorator for packet level annotation. '''
  def pkt_annt_decorator(klass):
    ''' Puts the class in the packet level dictionary. '''
    __packet_level_annotations[name] = klass
    return klass
  return pkt_annt_decorator

def field_level_annotation(name):
  ''' Decorator for field level annotation. '''
  def fld_annt_decorator(klass):
    ''' Puts the class in the field level dictionary. '''
    __field_level_annotations[name] = klass
    return klass
  return fld_annt_decorator

class Annotation(object):  # pylint: disable=R0903
  ''' Annotations representing the processor part of . '''
  def __init__(self, model):
    ''' @param model Is the the annotation model parsed in packet. '''
    self._model = model

def create_packet_level_annotation(packet, annotation_model):
  ''' Creates a packet level annotation. '''
  assert packet and annotation_model, \
      'Packet and annotation model cannot be None.'
  annot_class = __packet_level_annotations.get(annotation_model.name)
  if not annot_class:
    raise Exception('No such annotation: %s' % annotation_model.name)

  return annot_class(packet, annotation_model)

def create_field_level_annotation(field, annotation_model):
  ''' Creates a field level annotation. '''
  assert field and annotation_model, \
      'Field and annotation model cannot be None.'
  annot_class = __field_level_annotations.get(annotation_model.name)
  if not annot_class:
    raise Exception('Annotation not found: %s' % annotation_model.name)

  return annot_class(field, annotation_model)

class PacketLevelAnnotation(Annotation):  # pylint: disable=R0903
  ''' Annotations that are applied to a packet. '''
  def __init__(self, packet, model):
    Annotation.__init__(self, model)
    self._packet = packet

class FieldLevelAnnotation(Annotation):  # pylint: disable=R0903
  ''' Annotation that are applied to a field of a packet. '''
  def __init__(self, field, model):
    Annotation.__init__(self, model)
    self._field = field

@packet_level_annotation('type_selector')
class TypeSelectorAnnotation(PacketLevelAnnotation):
  ''' type_selector is used by derived packets to specify the selector
      condition. '''
  def __init__(self, packet, model):
    PacketLevelAnnotation.__init__(self, packet, model)

  def __find_field(self, name):
    ''' Finds a field in the packet hierarchy, otherwise return None. '''
    pkt = self._packet.parent  # We start from the parent packet.
    field = None
    while pkt and not field:
      field = pkt.find_field(name)
      pkt = pkt.parent
    return field

  def get_condition(self):
    ''' Returns a list of tuples from field to value. '''
    cond = []
    for param in self._model.params:
      field = self.__find_field(param.name)
      if not field:
        raise Exception('Field of type_selector not found: %s.%s' %
                        (self._packet.name, param.name))
      if param.value == None:
        raise Exception('type_selector does not have a value: %s' %
                        self._packet.name)
      cond.append((field, param.value))
    return cond


@packet_level_annotation('custom_size')  # pylint: disable=R0903
class CustomSizeAnnotation(PacketLevelAnnotation):
  ''' custom_size is used for packets that their size must be calculated by an
      external implementation. '''
  def __init__(self, packet, model):
    PacketLevelAnnotation.__init__(self, packet, model)
    packet.size_info = (True, None)


@packet_level_annotation('padded')  # pylint: disable=R0903
class PaddedAnnotation(PacketLevelAnnotation):
  ''' Padded is used for padded structures. It has two parameters:
      1) multiple: The structure length should be padded to be a multiple of
        "multiple".
      2) excluded: Whether to include the paddings in packet's size. '''
  def __init__(self, packet, model):
    PacketLevelAnnotation.__init__(self, packet, model)
    self.excluded = False
    for param in self._model.params:
      if param.name == 'multiple':
        self.multiple = int(param.value)
      elif param.name == 'excluded':
        self.excluded = True

@packet_level_annotation('bigendian')  # pylint: disable=R0903
class EndianAnnotation(PacketLevelAnnotation):
  ''' Used for annotate big endian packets.
      Note: All derived packets of a bigendian packets are big endian. '''
  def __init__(self, packet, model):
    PacketLevelAnnotation.__init__(self, packet, model)
    packet.big_endian = True

@field_level_annotation('size')  # pylint: disable=R0903
class SizeAnnotation(FieldLevelAnnotation):
  ''' @size is used for a field storing a packet's size or the size of another
      repreated field in bytes. In the latter case, user need to pass the field
      name as the parameter (e.g., @size(field)). Packet runtime automatically
      sets size in the respective packet/field.
      Note: size cannot be overriden in the child classes. '''
  def __init__(self, field, model):
    FieldLevelAnnotation.__init__(self, field, model)
    assert len(model.params) <= 1, \
        '@size can have at most one parameter: %s' % field.name
    if len(model.params) == 1:
      # TODO(soheil): We need to make sure that the field is a vector
      referencing_field = field.packet.find_field(model.params[0].name)
      assert referencing_field, 'Referenced field %s not found in %s' % \
          (field.name, model.params[0].name)
      referencing_field.set_repeated_info(size_field=field)
    else:
      field.packet.size_info = (True, field)

@field_level_annotation('count')  # pylint: disable=R0903
class CountAnnotation(FieldLevelAnnotation):
  ''' @count is used for a field storing the number of items in another
      repreated field. In the latter case, user need to pass the field
      name as the parameter (e.g., @count(field)). Packet runtime automatically
      sets count in the respective field.
      Note: count cannot be overriden in the child classes. '''
  def __init__(self, field, model):
    FieldLevelAnnotation.__init__(self, field, model)
    assert len(model.params) <= 1, \
        '@count can have at most one parameter: %s' % field.name
    if len(model.params) == 1:
      # TODO(soheil): We need to make sure that the field is a vector
      referencing_field = field.packet.find_field(model.params[0].name)
      referencing_field.set_repeated_info(count_field=field)
    else:
      field.packet.size_info = (True, field)

@field_level_annotation('repeated')  # pylint: disable=R0903
class RepeatedAnnotation(FieldLevelAnnotation):
  ''' The repeated annotation is used for annotate arrays. Each repeated field
      must have another field annotated with size accordingly.'''
  def __init__(self, field, model):
    FieldLevelAnnotation.__init__(self, field, model)

    if field.repeated_info:
      # This field had a @size field.
      assert len(model.params) == 0, \
          'Repeated field %s already has a size or count field.' % field.name
      return

    if len(model.params) == 0:
      field.set_repeated_info()
      return

    assert model.params[0].name == 'count', \
        '@repeated only accepts "count" as its parameter: %s' % field.name
    assert model.params[0].value != None, \
        'count in @repeated is None: %s.%s' % (field.packet.name, field.name)

    field.set_repeated_info(count=int(model.params[0].value))

