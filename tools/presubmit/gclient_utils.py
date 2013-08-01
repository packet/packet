# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Generic utils."""

import errno
import logging
import os
import Queue
import re
import stat
import sys
import tempfile
import threading
import time
import urlparse

import subprocess2


class Error(Exception):
  """gclient exception class."""
  pass


def SplitUrlRevision(url):
  """Splits url and returns a two-tuple: url, rev"""
  if url.startswith('ssh:'):
    # Make sure ssh://user-name@example.com/~/test.git@stable works
    regex = r'(ssh://(?:[-\w]+@)?[-\w:\.]+/[-~\w\./]+)(?:@(.+))?'
    components = re.search(regex, url).groups()
  else:
    components = url.split('@', 1)
    if len(components) == 1:
      components += [None]
  return tuple(components)


def IsDateRevision(revision):
  """Returns true if the given revision is of the form "{ ... }"."""
  return bool(revision and re.match(r'^\{.+\}$', str(revision)))


def MakeDateRevision(date):
  """Returns a revision representing the latest revision before the given
  date."""
  return "{" + date + "}"


def SyntaxErrorToError(filename, e):
  """Raises a gclient_utils.Error exception with the human readable message"""
  try:
    # Try to construct a human readable error message
    if filename:
      error_message = 'There is a syntax error in %s\n' % filename
    else:
      error_message = 'There is a syntax error\n'
    error_message += 'Line #%s, character %s: "%s"' % (
        e.lineno, e.offset, re.sub(r'[\r\n]*$', '', e.text))
  except:
    # Something went wrong, re-raise the original exception
    raise e
  else:
    raise Error(error_message)


class PrintableObject(object):
  def __str__(self):
    output = ''
    for i in dir(self):
      if i.startswith('__'):
        continue
      output += '%s = %s\n' % (i, str(getattr(self, i, '')))
    return output


def FileRead(filename, mode='rU'):
  content = None
  f = open(filename, mode)
  try:
    content = f.read()
  finally:
    f.close()
  return content


def FileWrite(filename, content, mode='w'):
  f = open(filename, mode)
  try:
    f.write(content)
  finally:
    f.close()


def rmtree(path):
  """shutil.rmtree() on steroids.

  Recursively removes a directory, even if it's marked read-only.

  shutil.rmtree() doesn't work on Windows if any of the files or directories
  are read-only, which svn repositories and some .svn files are.  We need to
  be able to force the files to be writable (i.e., deletable) as we traverse
  the tree.

  Even with all this, Windows still sometimes fails to delete a file, citing
  a permission error (maybe something to do with antivirus scans or disk
  indexing).  The best suggestion any of the user forums had was to wait a
  bit and try again, so we do that too.  It's hand-waving, but sometimes it
  works. :/

  On POSIX systems, things are a little bit simpler.  The modes of the files
  to be deleted doesn't matter, only the modes of the directories containing
  them are significant.  As the directory tree is traversed, each directory
  has its mode set appropriately before descending into it.  This should
  result in the entire tree being removed, with the possible exception of
  *path itself, because nothing attempts to change the mode of its parent.
  Doing so would be hazardous, as it's not a directory slated for removal.
  In the ordinary case, this is not a problem: for our purposes, the user
  will never lack write permission on *path's parent.
  """
  if not os.path.exists(path):
    return

  if os.path.islink(path) or not os.path.isdir(path):
    raise Error('Called rmtree(%s) in non-directory' % path)

  if sys.platform == 'win32':
    # Some people don't have the APIs installed. In that case we'll do without.
    win32api = None
    win32con = None
    try:
      # Unable to import 'XX'
      # pylint: disable=F0401
      import win32api, win32con
    except ImportError:
      pass
  else:
    # On POSIX systems, we need the x-bit set on the directory to access it,
    # the r-bit to see its contents, and the w-bit to remove files from it.
    # The actual modes of the files within the directory is irrelevant.
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

  def remove(func, subpath):
    if sys.platform == 'win32':
      os.chmod(subpath, stat.S_IWRITE)
      if win32api and win32con:
        win32api.SetFileAttributes(subpath, win32con.FILE_ATTRIBUTE_NORMAL)
    try:
      func(subpath)
    except OSError, e:
      if e.errno != errno.EACCES or sys.platform != 'win32':
        raise
      # Failed to delete, try again after a 100ms sleep.
      time.sleep(0.1)
      func(subpath)

  for fn in os.listdir(path):
    # If fullpath is a symbolic link that points to a directory, isdir will
    # be True, but we don't want to descend into that as a directory, we just
    # want to remove the link.  Check islink and treat links as ordinary files
    # would be treated regardless of what they reference.
    fullpath = os.path.join(path, fn)
    if os.path.islink(fullpath) or not os.path.isdir(fullpath):
      remove(os.remove, fullpath)
    else:
      # Recurse.
      rmtree(fullpath)

  remove(os.rmdir, path)

# TODO(maruel): Rename the references.
RemoveDirectory = rmtree


def safe_makedirs(tree):
  """Creates the directory in a safe manner.

  Because multiple threads can create these directories concurently, trap the
  exception and pass on.
  """
  count = 0
  while not os.path.exists(tree):
    count += 1
    try:
      os.makedirs(tree)
    except OSError, e:
      # 17 POSIX, 183 Windows
      if e.errno not in (17, 183):
        raise
      if count > 40:
        # Give up.
        raise


def CheckCallAndFilterAndHeader(args, always=False, **kwargs):
  """Adds 'header' support to CheckCallAndFilter.

  If |always| is True, a message indicating what is being done
  is printed to stdout all the time even if not output is generated. Otherwise
  the message header is printed only if the call generated any ouput.
  """
  stdout = kwargs.get('stdout', None) or sys.stdout
  if always:
    stdout.write('\n________ running \'%s\' in \'%s\'\n'
        % (' '.join(args), kwargs.get('cwd', '.')))
  else:
    filter_fn = kwargs.get('filter_fn', None)
    def filter_msg(line):
      if line is None:
        stdout.write('\n________ running \'%s\' in \'%s\'\n'
            % (' '.join(args), kwargs.get('cwd', '.')))
      elif filter_fn:
        filter_fn(line)
    kwargs['filter_fn'] = filter_msg
    kwargs['call_filter_on_first_line'] = True
  # Obviously.
  kwargs['print_stdout'] = True
  return CheckCallAndFilter(args, **kwargs)


class Wrapper(object):
  """Wraps an object, acting as a transparent proxy for all properties by
  default.
  """
  def __init__(self, wrapped):
    self._wrapped = wrapped

  def __getattr__(self, name):
    return getattr(self._wrapped, name)


class AutoFlush(Wrapper):
  """Creates a file object clone to automatically flush after N seconds."""
  def __init__(self, wrapped, delay):
    super(AutoFlush, self).__init__(wrapped)
    if not hasattr(self, 'lock'):
      self.lock = threading.Lock()
    self.__last_flushed_at = time.time()
    self.delay = delay

  @property
  def autoflush(self):
    return self

  def write(self, out, *args, **kwargs):
    self._wrapped.write(out, *args, **kwargs)
    should_flush = False
    self.lock.acquire()
    try:
      if self.delay and (time.time() - self.__last_flushed_at) > self.delay:
        should_flush = True
        self.__last_flushed_at = time.time()
    finally:
      self.lock.release()
    if should_flush:
      self.flush()


class Annotated(Wrapper):
  """Creates a file object clone to automatically prepends every line in worker
  threads with a NN> prefix.
  """
  def __init__(self, wrapped, include_zero=False):
    super(Annotated, self).__init__(wrapped)
    if not hasattr(self, 'lock'):
      self.lock = threading.Lock()
    self.__output_buffers = {}
    self.__include_zero = include_zero

  @property
  def annotated(self):
    return self

  def write(self, out):
    index = getattr(threading.currentThread(), 'index', 0)
    if not index and not self.__include_zero:
      # Unindexed threads aren't buffered.
      return self._wrapped.write(out)

    self.lock.acquire()
    try:
      # Use a dummy array to hold the string so the code can be lockless.
      # Strings are immutable, requiring to keep a lock for the whole dictionary
      # otherwise. Using an array is faster than using a dummy object.
      if not index in self.__output_buffers:
        obj = self.__output_buffers[index] = ['']
      else:
        obj = self.__output_buffers[index]
    finally:
      self.lock.release()

    # Continue lockless.
    obj[0] += out
    while '\n' in obj[0]:
      line, remaining = obj[0].split('\n', 1)
      if line:
        self._wrapped.write('%d>%s\n' % (index, line))
      obj[0] = remaining

  def flush(self):
    """Flush buffered output."""
    orphans = []
    self.lock.acquire()
    try:
      # Detect threads no longer existing.
      indexes = (getattr(t, 'index', None) for t in threading.enumerate())
      indexes = filter(None, indexes)
      for index in self.__output_buffers:
        if not index in indexes:
          orphans.append((index, self.__output_buffers[index][0]))
      for orphan in orphans:
        del self.__output_buffers[orphan[0]]
    finally:
      self.lock.release()

    # Don't keep the lock while writting. Will append \n when it shouldn't.
    for orphan in orphans:
      if orphan[1]:
        self._wrapped.write('%d>%s\n' % (orphan[0], orphan[1]))
    return self._wrapped.flush()


def MakeFileAutoFlush(fileobj, delay=10):
  autoflush = getattr(fileobj, 'autoflush', None)
  if autoflush:
    autoflush.delay = delay
    return fileobj
  return AutoFlush(fileobj, delay)


def MakeFileAnnotated(fileobj, include_zero=False):
  if getattr(fileobj, 'annotated', None):
    return fileobj
  return Annotated(fileobj)


def CheckCallAndFilter(args, stdout=None, filter_fn=None,
                       print_stdout=None, call_filter_on_first_line=False,
                       **kwargs):
  """Runs a command and calls back a filter function if needed.

  Accepts all subprocess2.Popen() parameters plus:
    print_stdout: If True, the command's stdout is forwarded to stdout.
    filter_fn: A function taking a single string argument called with each line
               of the subprocess2's output. Each line has the trailing newline
               character trimmed.
    stdout: Can be any bufferable output.

  stderr is always redirected to stdout.
  """
  assert print_stdout or filter_fn
  stdout = stdout or sys.stdout
  filter_fn = filter_fn or (lambda x: None)
  kid = subprocess2.Popen(
      args, bufsize=0, stdout=subprocess2.PIPE, stderr=subprocess2.STDOUT,
      **kwargs)

  # Do a flush of stdout before we begin reading from the subprocess2's stdout
  stdout.flush()

  # Also, we need to forward stdout to prevent weird re-ordering of output.
  # This has to be done on a per byte basis to make sure it is not buffered:
  # normally buffering is done for each line, but if svn requests input, no
  # end-of-line character is output after the prompt and it would not show up.
  try:
    in_byte = kid.stdout.read(1)
    if in_byte:
      if call_filter_on_first_line:
        filter_fn(None)
      in_line = ''
      while in_byte:
        if in_byte != '\r':
          if print_stdout:
            stdout.write(in_byte)
          if in_byte != '\n':
            in_line += in_byte
          else:
            filter_fn(in_line)
            in_line = ''
        else:
          filter_fn(in_line)
          in_line = ''
        in_byte = kid.stdout.read(1)
      # Flush the rest of buffered output. This is only an issue with
      # stdout/stderr not ending with a \n.
      if len(in_line):
        filter_fn(in_line)
    rv = kid.wait()
  except KeyboardInterrupt:
    print >> sys.stderr, 'Failed while running "%s"' % ' '.join(args)
    raise

  if rv:
    raise subprocess2.CalledProcessError(
        rv, args, kwargs.get('cwd', None), None, None)
  return 0


def FindGclientRoot(from_dir, filename='.gclient'):
  """Tries to find the gclient root."""
  real_from_dir = os.path.realpath(from_dir)
  path = real_from_dir
  while not os.path.exists(os.path.join(path, filename)):
    split_path = os.path.split(path)
    if not split_path[1]:
      return None
    path = split_path[0]

  # If we did not find the file in the current directory, make sure we are in a
  # sub directory that is controlled by this configuration.
  if path != real_from_dir:
    entries_filename = os.path.join(path, filename + '_entries')
    if not os.path.exists(entries_filename):
      # If .gclient_entries does not exist, a previous call to gclient sync
      # might have failed. In that case, we cannot verify that the .gclient
      # is the one we want to use. In order to not to cause too much trouble,
      # just issue a warning and return the path anyway.
      print >> sys.stderr, ("%s file in parent directory %s might not be the "
          "file you want to use" % (filename, path))
      return path
    scope = {}
    try:
      exec(FileRead(entries_filename), scope)
    except SyntaxError, e:
      SyntaxErrorToError(filename, e)
    all_directories = scope['entries'].keys()
    path_to_check = real_from_dir[len(path)+1:]
    while path_to_check:
      if path_to_check in all_directories:
        return path
      path_to_check = os.path.dirname(path_to_check)
    return None

  logging.info('Found gclient root at ' + path)
  return path


def PathDifference(root, subpath):
  """Returns the difference subpath minus root."""
  root = os.path.realpath(root)
  subpath = os.path.realpath(subpath)
  if not subpath.startswith(root):
    return None
  # If the root does not have a trailing \ or /, we add it so the returned
  # path starts immediately after the seperator regardless of whether it is
  # provided.
  root = os.path.join(root, '')
  return subpath[len(root):]


def FindFileUpwards(filename, path=None):
  """Search upwards from the a directory (default: current) to find a file.
  
  Returns nearest upper-level directory with the passed in file.
  """
  if not path:
    path = os.getcwd()
  path = os.path.realpath(path)
  while True:
    file_path = os.path.join(path, filename)
    if os.path.exists(file_path):
      return path
    (new_path, _) = os.path.split(path)
    if new_path == path:
      return None
    path = new_path


def GetGClientRootAndEntries(path=None):
  """Returns the gclient root and the dict of entries."""
  config_file = '.gclient_entries'
  root = FindFileUpwards(config_file, path)
  if not root:
    print "Can't find %s" % config_file
    return None
  config_path = os.path.join(root, config_file)
  env = {}
  execfile(config_path, env)
  config_dir = os.path.dirname(config_path)
  return config_dir, env['entries']


def lockedmethod(method):
  """Method decorator that holds self.lock for the duration of the call."""
  def inner(self, *args, **kwargs):
    try:
      try:
        self.lock.acquire()
      except KeyboardInterrupt:
        print >> sys.stderr, 'Was deadlocked'
        raise
      return method(self, *args, **kwargs)
    finally:
      self.lock.release()
  return inner


class WorkItem(object):
  """One work item."""
  # On cygwin, creating a lock throwing randomly when nearing ~100 locks.
  # As a workaround, use a single lock. Yep you read it right. Single lock for
  # all the 100 objects.
  lock = threading.Lock()

  def __init__(self, name):
    # A unique string representing this work item.
    self._name = name

  def run(self, work_queue):
    """work_queue is passed as keyword argument so it should be
    the last parameters of the function when you override it."""
    pass

  @property
  def name(self):
    return self._name


class ExecutionQueue(object):
  """Runs a set of WorkItem that have interdependencies and were WorkItem are
  added as they are processed.

  In gclient's case, Dependencies sometime needs to be run out of order due to
  From() keyword. This class manages that all the required dependencies are run
  before running each one.

  Methods of this class are thread safe.
  """
  def __init__(self, jobs, progress):
    """jobs specifies the number of concurrent tasks to allow. progress is a
    Progress instance."""
    # Set when a thread is done or a new item is enqueued.
    self.ready_cond = threading.Condition()
    # Maximum number of concurrent tasks.
    self.jobs = jobs
    # List of WorkItem, for gclient, these are Dependency instances.
    self.queued = []
    # List of strings representing each Dependency.name that was run.
    self.ran = []
    # List of items currently running.
    self.running = []
    # Exceptions thrown if any.
    self.exceptions = Queue.Queue()
    # Progress status
    self.progress = progress
    if self.progress:
      self.progress.update(0)

  def enqueue(self, d):
    """Enqueue one Dependency to be executed later once its requirements are
    satisfied.
    """
    assert isinstance(d, WorkItem)
    self.ready_cond.acquire()
    try:
      self.queued.append(d)
      total = len(self.queued) + len(self.ran) + len(self.running)
      logging.debug('enqueued(%s)' % d.name)
      if self.progress:
        self.progress._total = total + 1
        self.progress.update(0)
      self.ready_cond.notifyAll()
    finally:
      self.ready_cond.release()

  def flush(self, *args, **kwargs):
    """Runs all enqueued items until all are executed."""
    kwargs['work_queue'] = self
    self.ready_cond.acquire()
    try:
      while True:
        # Check for task to run first, then wait.
        while True:
          if not self.exceptions.empty():
            # Systematically flush the queue when an exception logged.
            self.queued = []
          self._flush_terminated_threads()
          if (not self.queued and not self.running or
              self.jobs == len(self.running)):
            logging.debug('No more worker threads or can\'t queue anything.')
            break

          # Check for new tasks to start.
          for i in xrange(len(self.queued)):
            # Verify its requirements.
            for r in self.queued[i].requirements:
              if not r in self.ran:
                # Requirement not met.
                break
            else:
              # Start one work item: all its requirements are satisfied.
              self._run_one_task(self.queued.pop(i), args, kwargs)
              break
          else:
            # Couldn't find an item that could run. Break out the outher loop.
            break

        if not self.queued and not self.running:
          # We're done.
          break
        # We need to poll here otherwise Ctrl-C isn't processed.
        try:
          self.ready_cond.wait(10)
        except KeyboardInterrupt:
          # Help debugging by printing some information:
          print >> sys.stderr, (
              ('\nAllowed parallel jobs: %d\n# queued: %d\nRan: %s\n'
                'Running: %d') % (
              self.jobs,
              len(self.queued),
              ', '.join(self.ran),
              len(self.running)))
          for i in self.queued:
            print >> sys.stderr, '%s: %s' % (i.name, ', '.join(i.requirements))
          raise
        # Something happened: self.enqueue() or a thread terminated. Loop again.
    finally:
      self.ready_cond.release()

    assert not self.running, 'Now guaranteed to be single-threaded'
    if not self.exceptions.empty():
      # To get back the stack location correctly, the raise a, b, c form must be
      # used, passing a tuple as the first argument doesn't work.
      e = self.exceptions.get()
      raise e[0], e[1], e[2]
    if self.progress:
      self.progress.end()

  def _flush_terminated_threads(self):
    """Flush threads that have terminated."""
    running = self.running
    self.running = []
    for t in running:
      if t.isAlive():
        self.running.append(t)
      else:
        t.join()
        sys.stdout.flush()
        if self.progress:
          self.progress.update(1, t.item.name)
        if t.item.name in self.ran:
          raise Error(
              'gclient is confused, "%s" is already in "%s"' % (
                t.item.name, ', '.join(self.ran)))
        if not t.item.name in self.ran:
          self.ran.append(t.item.name)

  def _run_one_task(self, task_item, args, kwargs):
    if self.jobs > 1:
      # Start the thread.
      index = len(self.ran) + len(self.running) + 1
      new_thread = self._Worker(task_item, index, args, kwargs)
      self.running.append(new_thread)
      new_thread.start()
    else:
      # Run the 'thread' inside the main thread. Don't try to catch any
      # exception.
      task_item.run(*args, **kwargs)
      self.ran.append(task_item.name)
      if self.progress:
        self.progress.update(1, ', '.join(t.item.name for t in self.running))

  class _Worker(threading.Thread):
    """One thread to execute one WorkItem."""
    def __init__(self, item, index, args, kwargs):
      threading.Thread.__init__(self, name=item.name or 'Worker')
      logging.info('_Worker(%s) reqs:%s' % (item.name, item.requirements))
      self.item = item
      self.index = index
      self.args = args
      self.kwargs = kwargs

    def run(self):
      """Runs in its own thread."""
      logging.debug('_Worker.run(%s)' % self.item.name)
      work_queue = self.kwargs['work_queue']
      try:
        self.item.run(*self.args, **self.kwargs)
      except Exception:
        # Catch exception location.
        logging.info('Caught exception in thread %s' % self.item.name)
        logging.info(str(sys.exc_info()))
        work_queue.exceptions.put(sys.exc_info())
      logging.info('_Worker.run(%s) done' % self.item.name)

      work_queue.ready_cond.acquire()
      try:
        work_queue.ready_cond.notifyAll()
      finally:
        work_queue.ready_cond.release()


def GetEditor(git):
  """Returns the most plausible editor to use."""
  if git:
    editor = os.environ.get('GIT_EDITOR')
  else:
    editor = os.environ.get('SVN_EDITOR')
  if not editor:
    editor = os.environ.get('EDITOR')
  if not editor:
    if sys.platform.startswith('win'):
      editor = 'notepad'
    else:
      editor = 'vim'
  return editor


def RunEditor(content, git):
  """Opens up the default editor in the system to get the CL description."""
  file_handle, filename = tempfile.mkstemp(text=True)
  # Make sure CRLF is handled properly by requiring none.
  if '\r' in content:
    print >> sys.stderr, (
        '!! Please remove \\r from your change description !!')
  fileobj = os.fdopen(file_handle, 'w')
  # Still remove \r if present.
  fileobj.write(re.sub('\r?\n', '\n', content))
  fileobj.close()

  try:
    cmd = '%s %s' % (GetEditor(git), filename)
    if sys.platform == 'win32' and os.environ.get('TERM') == 'msys':
      # Msysgit requires the usage of 'env' to be present.
      cmd = 'env ' + cmd
    try:
      # shell=True to allow the shell to handle all forms of quotes in
      # $EDITOR.
      subprocess2.check_call(cmd, shell=True)
    except subprocess2.CalledProcessError:
      return None
    return FileRead(filename)
  finally:
    os.remove(filename)


def UpgradeToHttps(url):
  """Upgrades random urls to https://.

  Do not touch unknown urls like ssh:// or git://.
  Do not touch http:// urls with a port number,
  Fixes invalid GAE url.
  """
  if not url:
    return url
  if not re.match(r'[a-z\-]+\://.*', url):
    # Make sure it is a valid uri. Otherwise, urlparse() will consider it a
    # relative url and will use http:///foo. Note that it defaults to http://
    # for compatibility with naked url like "localhost:8080".
    url = 'http://%s' % url
  parsed = list(urlparse.urlparse(url))
  # Do not automatically upgrade http to https if a port number is provided.
  if parsed[0] == 'http' and not re.match(r'^.+?\:\d+$', parsed[1]):
    parsed[0] = 'https'
  # Until GAE supports SNI, manually convert the url.
  if parsed[1] == 'codereview.chromium.org':
    parsed[1] = 'chromiumcodereview.appspot.com'
  return urlparse.urlunparse(parsed)


def ParseCodereviewSettingsContent(content):
  """Process a codereview.settings file properly."""
  lines = (l for l in content.splitlines() if not l.strip().startswith("#"))
  try:
    keyvals = dict([x.strip() for x in l.split(':', 1)] for l in lines if l)
  except ValueError:
    raise Error(
        'Failed to process settings, please fix. Content:\n\n%s' % content)
  def fix_url(key):
    if keyvals.get(key):
      keyvals[key] = UpgradeToHttps(keyvals[key])
  fix_url('CODE_REVIEW_SERVER')
  fix_url('VIEW_VC')
  return keyvals
