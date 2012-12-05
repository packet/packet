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
    packet = self._packet.parent  # We start from the parent packet.
    field = None
    while packet and not field:
      field = packet.find_field(name)
      packet = packet.parent
    return field

  def get_condition(self):
    ''' Returns a list of tuples from field to value. '''
    cond = []
    for param in self._model.params:
      field = self.__find_field(param.name)
      if not field:
        raise Exception('Field of type_selector not found: %s' % param.name)
      cond.append((field, param.value))
    return cond
