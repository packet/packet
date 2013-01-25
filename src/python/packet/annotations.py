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
    raise Exception('Annotation not found: %s' % annotation_model.name)

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
        raise Exception('Field of type_selector not found: %s' % param.name)
      if param.value == None:
        raise Exception('type_selector does not have a value: %s' %
                        self._packet.name)
      cond.append((field, param.value))
    return cond

@field_level_annotation('size')  # pylint: disable=R0903
class SizeAnnotation(FieldLevelAnnotation):
  ''' The size annotation is used for the field storing the size of its
      packet or another field. In the latter case, user need to pass the field
      name as the parameter (e.g., @size(field)). We set size_field in the
      respective packet/field.
      Note: size cannot be overriden in the child classes. '''
  def __init__(self, field, model):
    FieldLevelAnnotation.__init__(self, field, model)
    assert len(model.params) <= 1, \
        '@size can have at most one parameter: %s' % field.name
    if len(model.params) == 1:
      # TODO(soheil): We need to make sure that the field is a vector
      referencing_field = field.packet.find_field(model.params[0].name)
      referencing_field.repeated_info = (True, field)
    else:
      field.packet.size_info = (True, field)

@field_level_annotation('repeated')  # pylint: disable=R0903
class RepeatedAnnotation(FieldLevelAnnotation):
  ''' The repeated annotation is used for annotate arrays. Each repeated field
      must have another field annotated with size accordingly.'''
  def __init__(self, field, model):
    FieldLevelAnnotation.__init__(self, field, model)
    if len(model.params) == 1:
      assert model.params[0].name == 'size', \
          '@repeated only accepts "size" as its parameter: %s' % field.name
      field.repeated_info = (False, int(model.params[0].value))
    else:
      field.repeated_info = (True, None)

