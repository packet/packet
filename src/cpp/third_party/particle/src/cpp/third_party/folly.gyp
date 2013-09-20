#
# Copyright (C) 2012-2013, The Particle project authors.
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

{
  'variables': {
    'folly_home': 'folly',
    'folly_src_home': '<(folly_home)/folly',
  },
  'targets': [
    {
      'target_name': 'folly',
      'type': '<(library)',
      'include_dirs': [
        '<(folly_home)',
      ],
      'dependencies': [
        'boost.gyp:boost_common',
        'dconv.gyp:dconv',
        'gflags.gyp:gflags',
        'glog.gyp:glog',
      ],
      'all_dependent_settings': {
        'include_dirs': [
          '<(folly_home)',
        ],
      },
      'sources': [
        '<(folly_src_home)/ApplyTuple.h',
        '<(folly_src_home)/Arena.h',
        '<(folly_src_home)/Arena-inl.h',
        '<(folly_src_home)/AtomicHashArray.h',
        '<(folly_src_home)/AtomicHashArray-inl.h',
        '<(folly_src_home)/AtomicHashMap.h',
        '<(folly_src_home)/AtomicHashMap-inl.h',
        '<(folly_src_home)/Bits.cpp',
        '<(folly_src_home)/Bits.h',
        '<(folly_src_home)/Chrono.h',
        '<(folly_src_home)/ConcurrentSkipList.h',
        '<(folly_src_home)/ConcurrentSkipList-inl.h',
        '<(folly_src_home)/Conv.cpp',
        '<(folly_src_home)/Conv.h',
        '<(folly_src_home)/CpuId.h',
        '<(folly_src_home)/DiscriminatedPtr.h',
        '<(folly_src_home)/DynamicConverter.h',
        '<(folly_src_home)/dynamic.cpp',
        '<(folly_src_home)/dynamic.h',
        '<(folly_src_home)/dynamic-inl.h',
        '<(folly_src_home)/eventfd.h',
        '<(folly_src_home)/Exception.h',
        '<(folly_src_home)/FBString.h',
        '<(folly_src_home)/FBVector.h',
        '<(folly_src_home)/File.cpp',
        '<(folly_src_home)/File.h',
        '<(folly_src_home)/FileUtil.cpp',
        '<(folly_src_home)/FileUtil.h',
        '<(folly_src_home)/Fingerprint.h',
        '<(folly_src_home)/Foreach.h',
        '<(folly_src_home)/FormatArg.h',
        '<(folly_src_home)/Format.cpp',
        '<(folly_src_home)/Format.h',
        '<(folly_src_home)/Format-inl.h',
        '<(folly_src_home)/GroupVarint.cpp',
        '<(folly_src_home)/GroupVarint.h',
        '<(folly_src_home)/Hash.h',
        '<(folly_src_home)/Histogram.h',
        '<(folly_src_home)/Histogram-inl.h',
        '<(folly_src_home)/IntrusiveList.h',
        '<(folly_src_home)/json.cpp',
        '<(folly_src_home)/json.h',
        '<(folly_src_home)/Lazy.h',
        '<(folly_src_home)/Likely.h',
        '<(folly_src_home)/Logging.h',
        '<(folly_src_home)/Malloc.h',
        '<(folly_src_home)/MapUtil.h',
        '<(folly_src_home)/Memory.h',
        '<(folly_src_home)/MemoryMapping.cpp',
        '<(folly_src_home)/MemoryMapping.h',
        '<(folly_src_home)/MPMCQueue.h',
        '<(folly_src_home)/Optional.h',
        '<(folly_src_home)/PackedSyncPtr.h',
        '<(folly_src_home)/Padded.h',
        '<(folly_src_home)/Portability.h',
        '<(folly_src_home)/Preprocessor.h',
        '<(folly_src_home)/ProducerConsumerQueue.h',
        '<(folly_src_home)/Random.cpp',
        '<(folly_src_home)/Random.h',
        #'<(folly_src_home)/Range.cpp',
        '<(folly_src_home)/Range.h',
        '<(folly_src_home)/RWSpinLock.h',
        '<(folly_src_home)/ScopeGuard.h',
        '<(folly_src_home)/SmallLocks.h',
        '<(folly_src_home)/small_vector.h',
        '<(folly_src_home)/sorted_vector_types.h',
        '<(folly_src_home)/SpookyHash.cpp',
        '<(folly_src_home)/SpookyHash.h',
        '<(folly_src_home)/SpookyHashV1.cpp',
        '<(folly_src_home)/SpookyHashV1.h',
        '<(folly_src_home)/SpookyHashV2.cpp',
        '<(folly_src_home)/SpookyHashV2.h',
        '<(folly_src_home)/StlAllocator.h',
        '<(folly_src_home)/String.cpp',
        '<(folly_src_home)/String.h',
        '<(folly_src_home)/String-inl.h',
        '<(folly_src_home)/Subprocess.cpp',
        '<(folly_src_home)/Subprocess.h',
        '<(folly_src_home)/Synchronized.h',
        '<(folly_src_home)/ThreadCachedArena.cpp',
        '<(folly_src_home)/ThreadCachedArena.h',
        '<(folly_src_home)/ThreadCachedInt.h',
        '<(folly_src_home)/ThreadLocal.h',
        '<(folly_src_home)/TimeoutQueue.cpp',
        '<(folly_src_home)/TimeoutQueue.h',
        '<(folly_src_home)/Traits.h',
        '<(folly_src_home)/Unicode.cpp',
        '<(folly_src_home)/Unicode.h',
        '<(folly_src_home)/Uri.cpp',
        '<(folly_src_home)/Uri.h',
        '<(folly_src_home)/Uri-inl.h',
      ],
    },
  ]
}
