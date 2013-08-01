# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Generic presubmit checks that can be reused by other presubmit checks."""


### Description checks

def CheckChangeHasTestField(input_api, output_api):
  """Requires that the changelist have a TEST= field."""
  if input_api.change.TEST:
    return []
  else:
    return [output_api.PresubmitNotifyResult(
        'If this change requires manual test instructions to QA team, add '
        'TEST=[instructions].')]


def CheckChangeHasBugField(input_api, output_api):
  """Requires that the changelist have a BUG= field."""
  if input_api.change.BUG:
    return []
  else:
    return [output_api.PresubmitNotifyResult(
        'If this change has an associated bug, add BUG=[bug number].')]


def CheckChangeHasTestedField(input_api, output_api):
  """Requires that the changelist have a TESTED= field."""
  if input_api.change.TESTED:
    return []
  else:
    return [output_api.PresubmitError('Changelist must have a TESTED= field.')]


def CheckChangeHasQaField(input_api, output_api):
  """Requires that the changelist have a QA= field."""
  if input_api.change.QA:
    return []
  else:
    return [output_api.PresubmitError('Changelist must have a QA= field.')]


def CheckDoNotSubmitInDescription(input_api, output_api):
  """Checks that the user didn't add 'DO NOT ' + 'SUBMIT' to the CL description.
  """
  keyword = 'DO NOT ' + 'SUBMIT'
  if keyword in input_api.change.DescriptionText():
    return [output_api.PresubmitError(
        keyword + ' is present in the changelist description.')]
  else:
    return []


def CheckChangeHasDescription(input_api, output_api):
  """Checks the CL description is not empty."""
  text = input_api.change.DescriptionText()
  if text.strip() == '':
    if input_api.is_committing:
      return [output_api.PresubmitError('Add a description.')]
    else:
      return [output_api.PresubmitNotifyResult('Add a description.')]
  return []


def CheckChangeWasUploaded(input_api, output_api):
  """Checks that the issue was uploaded before committing."""
  if input_api.is_committing and not input_api.change.issue:
    return [output_api.PresubmitError(
      'Issue wasn\'t uploaded. Please upload first.')]
  return []


### Content checks

def CheckDoNotSubmitInFiles(input_api, output_api):
  """Checks that the user didn't add 'DO NOT ' + 'SUBMIT' to any files."""
  # We want to check every text file, not just source files.
  file_filter = lambda x : x
  keyword = 'DO NOT ' + 'SUBMIT'
  errors = _FindNewViolationsOfRule(lambda _, line : keyword not in line,
                                    input_api, file_filter)
  text = '\n'.join('Found %s in %s' % (keyword, loc) for loc in errors)
  if text:
    return [output_api.PresubmitError(text)]
  return []


def CheckChangeLintsClean(input_api, output_api, source_file_filter=None):
  """Checks that all '.cc' and '.h' files pass cpplint.py."""
  _RE_IS_TEST = input_api.re.compile(r'.*tests?.(cc|h)$')
  result = []

  # Initialize cpplint.
  import cpplint
  # Access to a protected member _XX of a client class
  # pylint: disable=W0212
  cpplint._cpplint_state.ResetErrorCounts()

  # Justifications for each filter:
  #
  # - build/include       : Too many; fix in the future.
  # - build/include_order : Not happening; #ifdefed includes.
  # - build/namespace     : I'm surprised by how often we violate this rule.
  # - readability/casting : Mistakes a whole bunch of function pointer.
  # - runtime/int         : Can be fixed long term; volume of errors too high
  # - runtime/virtual     : Broken now, but can be fixed in the future?
  # - whitespace/braces   : We have a lot of explicit scoping in chrome code.
  cpplint._SetFilters('-build/include,-build/include_order,-build/namespace,'
                      '-readability/casting,-runtime/int,-runtime/virtual,'
                      '-whitespace/braces')

  # We currently are more strict with normal code than unit tests; 4 and 5 are
  # the verbosity level that would normally be passed to cpplint.py through
  # --verbose=#. Hopefully, in the future, we can be more verbose.
  files = [f.AbsoluteLocalPath() for f in
           input_api.AffectedSourceFiles(source_file_filter)]
  for file_name in files:
    if _RE_IS_TEST.match(file_name):
      level = 5
    else:
      level = 4

    cpplint.ProcessFile(file_name, level)

  if cpplint._cpplint_state.error_count > 0:
    if input_api.is_committing:
      res_type = output_api.PresubmitError
    else:
      res_type = output_api.PresubmitPromptWarning
    result = [res_type('Changelist failed cpplint.py check.')]

  return result


def CheckChangeHasNoCR(input_api, output_api, source_file_filter=None):
  """Checks no '\r' (CR) character is in any source files."""
  cr_files = []
  for f in input_api.AffectedSourceFiles(source_file_filter):
    if '\r' in input_api.ReadFile(f, 'rb'):
      cr_files.append(f.LocalPath())
  if cr_files:
    return [output_api.PresubmitPromptWarning(
        'Found a CR character in these files:', items=cr_files)]
  return []


def CheckSvnModifiedDirectories(input_api, output_api, source_file_filter=None):
  """Checks for files in svn modified directories.

  They will get submitted on accident because svn commits recursively by
  default, and that's very dangerous.
  """
  if input_api.change.scm != 'svn':
    return []

  errors = []
  current_cl_files = input_api.change.GetModifiedFiles()
  all_modified_files = input_api.change.GetAllModifiedFiles()
  # Filter out files in the current CL.
  modified_files = [f for f in all_modified_files if f not in current_cl_files]
  modified_abspaths = [input_api.os_path.abspath(f) for f in modified_files]

  for f in input_api.AffectedFiles(file_filter=source_file_filter):
    if f.Action() == 'M' and f.IsDirectory():
      curpath = f.AbsoluteLocalPath()
      bad_files = []
      # Check if any of the modified files in other CLs are under curpath.
      for i in xrange(len(modified_files)):
        abspath = modified_abspaths[i]
        if input_api.os_path.commonprefix([curpath, abspath]) == curpath:
          bad_files.append(modified_files[i])
      if bad_files:
        if input_api.is_committing:
          error_type = output_api.PresubmitPromptWarning
        else:
          error_type = output_api.PresubmitNotifyResult
        errors.append(error_type(
            'Potential accidental commits in changelist %s:' % f.LocalPath(),
            items=bad_files))
  return errors


def CheckChangeHasOnlyOneEol(input_api, output_api, source_file_filter=None):
  """Checks the files ends with one and only one \n (LF)."""
  eof_files = []
  for f in input_api.AffectedSourceFiles(source_file_filter):
    contents = input_api.ReadFile(f, 'rb')
    # Check that the file ends in one and only one newline character.
    if len(contents) > 1 and (contents[-1:] != '\n' or contents[-2:-1] == '\n'):
      eof_files.append(f.LocalPath())

  if eof_files:
    return [output_api.PresubmitPromptWarning(
      'These files should end in one (and only one) newline character:',
      items=eof_files)]
  return []


def CheckChangeHasNoCrAndHasOnlyOneEol(input_api, output_api,
                                       source_file_filter=None):
  """Runs both CheckChangeHasNoCR and CheckChangeHasOnlyOneEOL in one pass.

  It is faster because it is reading the file only once.
  """
  cr_files = []
  eof_files = []
  for f in input_api.AffectedSourceFiles(source_file_filter):
    contents = input_api.ReadFile(f, 'rb')
    if '\r' in contents:
      cr_files.append(f.LocalPath())
    # Check that the file ends in one and only one newline character.
    if len(contents) > 1 and (contents[-1:] != '\n' or contents[-2:-1] == '\n'):
      eof_files.append(f.LocalPath())
  outputs = []
  if cr_files:
    outputs.append(output_api.PresubmitPromptWarning(
        'Found a CR character in these files:', items=cr_files))
  if eof_files:
    outputs.append(output_api.PresubmitPromptWarning(
      'These files should end in one (and only one) newline character:',
      items=eof_files))
  return outputs


def _ReportErrorFileAndLine(filename, line_num, line):
  """Default error formatter for _FindNewViolationsOfRule."""
  return '%s, line %s' % (filename, line_num)


def _FindNewViolationsOfRule(callable_rule, input_api, source_file_filter=None,
                             error_formatter=_ReportErrorFileAndLine):
  """Find all newly introduced violations of a per-line rule (a callable).

  Arguments:
    callable_rule: a callable taking a file extension and line of input and
      returning True if the rule is satisfied and False if there was a problem.
    input_api: object to enumerate the affected files.
    source_file_filter: a filter to be passed to the input api.
    error_formatter: a callable taking (filename, line_number, line) and
      returning a formatted error string.

  Returns:
    A list of the newly-introduced violations reported by the rule.
  """
  errors = []
  for f in input_api.AffectedFiles(include_deletes=False,
                                   file_filter=source_file_filter):
    # For speed, we do two passes, checking first the full file.  Shelling out
    # to the SCM to determine the changed region can be quite expensive on
    # Win32.  Assuming that most files will be kept problem-free, we can
    # skip the SCM operations most of the time.
    extension = str(f.LocalPath()).rsplit('.', 1)[-1]
    if all(callable_rule(extension, line) for line in f.NewContents()):
      continue  # No violation found in full text: can skip considering diff.

    for line_num, line in f.ChangedContents():
      if not callable_rule(extension, line):
        errors.append(error_formatter(f.LocalPath(), line_num, line))

  return errors


def CheckChangeHasNoTabs(input_api, output_api, source_file_filter=None):
  """Checks that there are no tab characters in any of the text files to be
  submitted.
  """
  # In addition to the filter, make sure that makefiles are blacklisted.
  if not source_file_filter:
    # It's the default filter.
    source_file_filter = input_api.FilterSourceFile
  def filter_more(affected_file):
    return (not input_api.os_path.basename(affected_file.LocalPath()) in
                ('Makefile', 'makefile') and
            source_file_filter(affected_file))

  tabs = _FindNewViolationsOfRule(lambda _, line : '\t' not in line,
                                  input_api, filter_more)

  if tabs:
    return [output_api.PresubmitPromptWarning('Found a tab character in:',
                                              long_text='\n'.join(tabs))]
  return []


def CheckChangeTodoHasOwner(input_api, output_api, source_file_filter=None):
  """Checks that the user didn't add TODO(name) without an owner."""

  unowned_todo = input_api.re.compile('TO' + 'DO[^(]')
  errors = _FindNewViolationsOfRule(lambda _, x : not unowned_todo.search(x),
                                    input_api, source_file_filter)
  errors = ['Found TO' + 'DO with no owner in ' + x for x in errors]
  if errors:
    return [output_api.PresubmitPromptWarning('\n'.join(errors))]
  return []


def CheckChangeHasNoStrayWhitespace(input_api, output_api,
                                    source_file_filter=None):
  """Checks that there is no stray whitespace at source lines end."""
  errors = _FindNewViolationsOfRule(lambda _, line : line.rstrip() == line,
                                    input_api, source_file_filter)
  if errors:
    return [output_api.PresubmitPromptWarning(
        'Found line ending with white spaces in:',
        long_text='\n'.join(errors))]
  return []


def CheckLongLines(input_api, output_api, maxlen=80, source_file_filter=None):
  """Checks that there aren't any lines longer than maxlen characters in any of
  the text files to be submitted.
  """
  maxlens = { 
      'java': 100, 
      '': maxlen,
  }
  # Note: these are C++ specific but processed on all languages. :(
  MACROS = ('#define', '#include', '#import', '#pragma', '#if', '#endif')

  def no_long_lines(file_extension, line):
    file_maxlen = maxlens.get(file_extension, maxlens[''])
    # Stupidly long symbols that needs to be worked around if takes 66% of line.
    long_symbol = file_maxlen * 2 / 3
    # Hard line length limit at 50% more.
    extra_maxlen = file_maxlen * 3 / 2

    line_len = len(line)
    if line_len <= file_maxlen:
      return True

    if line_len > extra_maxlen:
      return False

    return (
        line.startswith(MACROS) or
        any((url in line) for url in ('http://', 'https://')) or
        input_api.re.match(
          r'.*[A-Za-z][A-Za-z_0-9]{%d,}.*' % long_symbol, line))

  def format_error(filename, line_num, line):
    return '%s, line %s, %s chars' % (filename, line_num, len(line))

  errors = _FindNewViolationsOfRule(no_long_lines, input_api,
                                    source_file_filter,
                                    error_formatter=format_error)
  if errors:
    msg = 'Found lines longer than %s characters (first 5 shown).' % maxlen
    return [output_api.PresubmitPromptWarning(msg, items=errors[:5])]
  else:
    return []


def CheckLicense(input_api, output_api, license_re, source_file_filter=None,
    accept_empty_files=True):
  """Verifies the license header.
  """
  license_re = input_api.re.compile(license_re, input_api.re.MULTILINE)
  bad_files = []
  for f in input_api.AffectedSourceFiles(source_file_filter):
    contents = input_api.ReadFile(f, 'rb')
    if accept_empty_files and not contents:
      continue
    if not license_re.search(contents):
      bad_files.append(f.LocalPath())
  if bad_files:
    if input_api.is_committing:
      res_type = output_api.PresubmitPromptWarning
    else:
      res_type = output_api.PresubmitNotifyResult
    return [res_type(
        'License must match:\n%s\n' % license_re.pattern +
        'Found a bad license header in these files:', items=bad_files)]
  return []


def CheckChangeSvnEolStyle(input_api, output_api, source_file_filter=None):
  """Checks that the source files have svn:eol-style=LF."""
  return CheckSvnProperty(input_api, output_api,
                          'svn:eol-style', 'LF',
                          input_api.AffectedSourceFiles(source_file_filter))


def CheckSvnForCommonMimeTypes(input_api, output_api):
  """Checks that common binary file types have the correct svn:mime-type."""
  output = []
  files = input_api.AffectedFiles(include_deletes=False)
  def IsExts(x, exts):
    path = x.LocalPath()
    for extension in exts:
      if path.endswith(extension):
        return True
    return False
  def FilterFiles(extension):
    return filter(lambda x: IsExts(x, extension), files)
  def RunCheck(mime_type, files):
    output.extend(CheckSvnProperty(input_api, output_api, 'svn:mime-type',
                                   mime_type, files))
  RunCheck('application/pdf', FilterFiles(['.pdf']))
  RunCheck('image/bmp', FilterFiles(['.bmp']))
  RunCheck('image/gif', FilterFiles(['.gif']))
  RunCheck('image/png', FilterFiles(['.png']))
  RunCheck('image/jpeg', FilterFiles(['.jpg', '.jpeg', '.jpe']))
  RunCheck('image/vnd.microsoft.icon', FilterFiles(['.ico']))
  return output


def CheckSvnProperty(input_api, output_api, prop, expected, affected_files):
  """Checks that affected_files files have prop=expected."""
  if input_api.change.scm != 'svn':
    return []

  bad = filter(lambda f: f.Property(prop) != expected, affected_files)
  if bad:
    if input_api.is_committing:
      res_type = output_api.PresubmitError
    else:
      res_type = output_api.PresubmitNotifyResult
    message = 'Run the command: svn pset %s %s \\' % (prop, expected)
    return [res_type(message, items=bad)]
  return []


### Other checks

def CheckDoNotSubmit(input_api, output_api):
  return (
      CheckDoNotSubmitInDescription(input_api, output_api) +
      CheckDoNotSubmitInFiles(input_api, output_api)
      )


def CheckTreeIsOpen(input_api, output_api,
                    url=None, closed=None, json_url=None):
  """Check whether to allow commit without prompt.

  Supports two styles:
    1. Checks that an url's content doesn't match a regexp that would mean that
       the tree is closed. (old)
    2. Check the json_url to decide whether to allow commit without prompt.
  Args:
    input_api: input related apis.
    output_api: output related apis.
    url: url to use for regex based tree status.
    closed: regex to match for closed status.
    json_url: url to download json style status.
  """
  if not input_api.is_committing:
    return []
  try:
    if json_url:
      connection = input_api.urllib2.urlopen(json_url)
      status = input_api.json.loads(connection.read())
      connection.close()
      if not status['can_commit_freely']:
        short_text = 'Tree state is: ' + status['general_state']
        long_text = status['message'] + '\n' + json_url
        return [output_api.PresubmitError(short_text, long_text=long_text)]
    else:
      # TODO(bradnelson): drop this once all users are gone.
      connection = input_api.urllib2.urlopen(url)
      status = connection.read()
      connection.close()
      if input_api.re.match(closed, status):
        long_text = status + '\n' + url
        return [output_api.PresubmitError('The tree is closed.',
                                          long_text=long_text)]
  except IOError as e:
    return [output_api.PresubmitError('Error fetching tree status.',
                                      long_text=str(e))]
  return []


def RunUnitTestsInDirectory(
    input_api, output_api, directory, whitelist=None, blacklist=None):
  """Lists all files in a directory and runs them. Doesn't recurse.

  It's mainly a wrapper for RunUnitTests. USe whitelist and blacklist to filter
  tests accordingly.
  """
  unit_tests = []
  test_path = input_api.os_path.abspath(
      input_api.os_path.join(input_api.PresubmitLocalPath(), directory))

  def check(filename, filters):
    return any(True for i in filters if input_api.re.match(i, filename))

  to_run = found = 0
  for filename in input_api.os_listdir(test_path):
    found += 1
    fullpath = input_api.os_path.join(test_path, filename)
    if not input_api.os_path.isfile(fullpath):
      continue
    if whitelist and not check(filename, whitelist):
      continue
    if blacklist and check(filename, blacklist):
      continue
    unit_tests.append(input_api.os_path.join(directory, filename))
    to_run += 1
  input_api.logging.debug('Found %d files, running %d' % (found, to_run))
  if not to_run:
    return [
        output_api.PresubmitPromptWarning(
          'Out of %d files, found none that matched w=%r, b=%r in directory %s'
          % (found, whitelist, blacklist, directory))
    ]
  return RunUnitTests(input_api, output_api, unit_tests)


def RunUnitTests(input_api, output_api, unit_tests):
  """Runs all unit tests in a directory.

  On Windows, sys.executable is used for unit tests ending with ".py".
  """
  # We don't want to hinder users from uploading incomplete patches.
  if input_api.is_committing:
    message_type = output_api.PresubmitError
  else:
    message_type = output_api.PresubmitPromptWarning

  results = []
  for unit_test in unit_tests:
    cmd = []
    if input_api.platform == 'win32' and unit_test.endswith('.py'):
      # Windows needs some help.
      cmd = [input_api.python_executable]
    cmd.append(unit_test)
    if input_api.verbose:
      print('Running %s' % unit_test)
      cmd.append('--verbose')
    try:
      if input_api.verbose:
        input_api.subprocess.check_call(cmd, cwd=input_api.PresubmitLocalPath())
      else:
        input_api.subprocess.check_output(
            cmd,
            stderr=input_api.subprocess.STDOUT,
            cwd=input_api.PresubmitLocalPath())
    except (OSError, input_api.subprocess.CalledProcessError), e:
      results.append(message_type('%s failed!\n%s' % (unit_test, e)))
  return results


def RunPythonUnitTests(input_api, output_api, unit_tests):
  """Run the unit tests out of process, capture the output and use the result
  code to determine success.

  DEPRECATED.
  """
  # We don't want to hinder users from uploading incomplete patches.
  if input_api.is_committing:
    message_type = output_api.PresubmitError
  else:
    message_type = output_api.PresubmitNotifyResult
  results = []
  for unit_test in unit_tests:
    # Run the unit tests out of process. This is because some unit tests
    # stub out base libraries and don't clean up their mess. It's too easy to
    # get subtle bugs.
    cwd = None
    env = None
    unit_test_name = unit_test
    # 'python -m test.unit_test' doesn't work. We need to change to the right
    # directory instead.
    if '.' in unit_test:
      # Tests imported in submodules (subdirectories) assume that the current
      # directory is in the PYTHONPATH. Manually fix that.
      unit_test = unit_test.replace('.', '/')
      cwd = input_api.os_path.dirname(unit_test)
      unit_test = input_api.os_path.basename(unit_test)
      env = input_api.environ.copy()
      # At least on Windows, it seems '.' must explicitly be in PYTHONPATH
      backpath = [
          '.', input_api.os_path.pathsep.join(['..'] * (cwd.count('/') + 1))
        ]
      if env.get('PYTHONPATH'):
        backpath.append(env.get('PYTHONPATH'))
      env['PYTHONPATH'] = input_api.os_path.pathsep.join((backpath))
    cmd = [input_api.python_executable, '-m', '%s' % unit_test]
    try:
      input_api.subprocess.check_output(
          cmd, stderr=input_api.subprocess.STDOUT, cwd=cwd, env=env)
    except (OSError, input_api.subprocess.CalledProcessError), e:
      results.append(message_type('%s failed!\n%s' % (unit_test_name, e)))
  return results


def _FetchAllFiles(input_api, white_list, black_list):
  """Hack to fetch all files."""
  # We cannot use AffectedFiles here because we want to test every python
  # file on each single python change. It's because a change in a python file
  # can break another unmodified file.
  # Use code similar to InputApi.FilterSourceFile()
  def Find(filepath, filters):
    for item in filters:
      if input_api.re.match(item, filepath):
        return True
    return False

  files = []
  path_len = len(input_api.PresubmitLocalPath())
  for dirpath, dirnames, filenames in input_api.os_walk(
      input_api.PresubmitLocalPath()):
    # Passes dirnames in black list to speed up search.
    for item in dirnames[:]:
      filepath = input_api.os_path.join(dirpath, item)[path_len + 1:]
      if Find(filepath, black_list):
        dirnames.remove(item)
    for item in filenames:
      filepath = input_api.os_path.join(dirpath, item)[path_len + 1:]
      if Find(filepath, white_list) and not Find(filepath, black_list):
        files.append(filepath)
  return files


def RunPylint(input_api, output_api, white_list=None, black_list=None):
  """Run pylint on python files.

  The default white_list enforces looking only a *.py files.
  """
  white_list = tuple(white_list or ('.*\.py$',))
  black_list = tuple(black_list or input_api.DEFAULT_BLACK_LIST)
  if input_api.is_committing:
    error_type = output_api.PresubmitError
  else:
    error_type = output_api.PresubmitPromptWarning

  # Only trigger if there is at least one python file affected.
  src_filter = lambda x: input_api.FilterSourceFile(x, white_list, black_list)
  if not input_api.AffectedSourceFiles(src_filter):
    return []

  # On certain pylint/python version combination, running pylint throws a lot of
  # warning messages.
  import warnings
  warnings.filterwarnings('ignore', category=DeprecationWarning)
  try:
    files = _FetchAllFiles(input_api, white_list, black_list)
    if not files:
      return []
    # Now that at least one python file was modified and all the python files
    # were listed, try to run pylint.
    try:
      from pylint import lint
      from pylint.utils import UnknownMessage
      input_api.logging.debug(
          'Using pylint v%s from %s' % (lint.version, lint.__file__))
    except ImportError:
      if input_api.platform == 'win32':
        return [output_api.PresubmitNotifyResult(
          'Warning: Can\'t run pylint because it is not installed. Please '
          'install manually\n'
          'Cannot do static analysis of python files.')]
      return [output_api.PresubmitError(
          'Please install pylint with "sudo apt-get install python-setuptools; '
          'sudo easy_install pylint"\n'
          'or visit http://pypi.python.org/pypi/setuptools.\n'
          'Cannot do static analysis of python files.')]

    def run_lint(files):
      try:
        lint.Run(files)
        assert False
      except SystemExit, e:
        # pylint has the bad habit of calling sys.exit(), trap it here.
        return e.code
      except UnknownMessage, e:
        return 'Please upgrade pylint: %s' % e

    result = None
    if not input_api.verbose:
      result = run_lint(sorted(files))
    else:
      for filename in sorted(files):
        print('Running pylint on %s' % filename)
        result = run_lint([filename]) or result
    if isinstance(result, basestring):
      return [error_type(result)]
    elif result:
      return [error_type('Fix pylint errors first.')]
    return []
  finally:
    warnings.filterwarnings('default', category=DeprecationWarning)


# TODO(dpranke): Get the host_url from the input_api instead
def CheckRietveldTryJobExecution(input_api, output_api, host_url, platforms,
                                 owner):
  # Temporarily 'fix' the check while the Rietveld API is being upgraded to
  # something sensible.
  return []


def CheckBuildbotPendingBuilds(input_api, output_api, url, max_pendings,
    ignored):
  if not input_api.json:
    return [output_api.PresubmitPromptWarning(
      'Please install simplejson or upgrade to python 2.6+')]
  try:
    connection = input_api.urllib2.urlopen(url)
    raw_data = connection.read()
    connection.close()
  except IOError:
    return [output_api.PresubmitNotifyResult('%s is not accessible' % url)]

  try:
    data = input_api.json.loads(raw_data)
  except ValueError:
    return [output_api.PresubmitNotifyResult('Received malformed json while '
                                             'looking up buildbot status')]

  out = []
  for (builder_name, builder) in data.iteritems():
    if builder_name in ignored:
      continue
    if builder.get('state', '') == 'offline':
      continue
    pending_builds_len = len(builder.get('pending_builds', []))
    if pending_builds_len > max_pendings:
      out.append('%s has %d build(s) pending' %
                  (builder_name, pending_builds_len))
  if out:
    return [output_api.PresubmitPromptWarning(
        'Build(s) pending. It is suggested to wait that no more than %d '
            'builds are pending.' % max_pendings,
        long_text='\n'.join(out))]
  return []


def CheckOwners(input_api, output_api, source_file_filter=None):
  if input_api.is_committing:
    if input_api.tbr:
      return [output_api.PresubmitNotifyResult(
          '--tbr was specified, skipping OWNERS check')]
    if not input_api.change.issue:
      return [output_api.PresubmitError("OWNERS check failed: this change has "
          "no Rietveld issue number, so we can't check it for approvals.")]
    needed = 'LGTM from an OWNER'
    output = output_api.PresubmitError
  else:
    needed = 'OWNER reviewers'
    output = output_api.PresubmitNotifyResult

  affected_files = set([f.LocalPath() for f in
      input_api.change.AffectedFiles(file_filter=source_file_filter)])

  owners_db = input_api.owners_db
  owner_email, reviewers = _RietveldOwnerAndReviewers(
      input_api,
      owners_db.email_regexp,
      approval_needed=input_api.is_committing)

  if owner_email:
    reviewers_plus_owner = reviewers.union(set([owner_email]))
  elif input_api.is_committing:
    return [output_api.PresubmitWarning(
        'The issue was not uploaded so you have no OWNER approval.')]
  else:
    owner_email = ''
    reviewers_plus_owner = set()

  missing_directories = owners_db.directories_not_covered_by(affected_files,
      reviewers_plus_owner)
  if missing_directories:
    return [output('Missing %s for files in these directories:\n    %s' %
                   (needed, '\n    '.join(missing_directories)))]

  if input_api.is_committing and not reviewers:
    return [output('Missing LGTM from someone other than %s' % owner_email)]
  return []


def _RietveldOwnerAndReviewers(input_api, email_regexp, approval_needed=False):
  """Return the owner and reviewers of a change, if any.

  If approval_needed is True, only reviewers who have approved the change
  will be returned.
  """
  if not input_api.change.issue:
    return None, None

  issue_props = input_api.rietveld.get_issue_properties(
      int(input_api.change.issue), True)
  if not approval_needed:
    return issue_props['owner_email'], set(issue_props['reviewers'])

  owner_email = issue_props['owner_email']

  def match_reviewer(r):
    return email_regexp.match(r) and r != owner_email

  messages = issue_props.get('messages', [])
  approvers = set(
      m['sender'] for m in messages
      if m.get('approval') and match_reviewer(m['sender']))

  return owner_email, approvers


def _CheckConstNSObject(input_api, output_api, source_file_filter):
  """Checks to make sure no objective-c files have |const NSSomeClass*|."""
  pattern = input_api.re.compile(
      r'const\s+NS(?!(Point|Range|Rect|Size)\s*\*)\w*\s*\*')

  def objective_c_filter(f):
    return (source_file_filter(f) and
            input_api.os_path.splitext(f.LocalPath())[1] in ('.h', '.m', '.mm'))

  files = []
  for f in input_api.AffectedSourceFiles(objective_c_filter):
    contents = input_api.ReadFile(f)
    if pattern.search(contents):
      files.append(f)

  if files:
    if input_api.is_committing:
      res_type = output_api.PresubmitPromptWarning
    else:
      res_type = output_api.PresubmitNotifyResult
    return [ res_type('|const NSClass*| is wrong, see ' +
                      'http://dev.chromium.org/developers/clang-mac',
                      files) ]
  return []


def _CheckSingletonInHeaders(input_api, output_api, source_file_filter):
  """Checks to make sure no header files have |Singleton<|."""
  pattern = input_api.re.compile(r'Singleton\s*<')
  files = []
  for f in input_api.AffectedSourceFiles(source_file_filter):
    if (f.LocalPath().endswith('.h') or f.LocalPath().endswith('.hxx') or
        f.LocalPath().endswith('.hpp') or f.LocalPath().endswith('.inl')):
      contents = input_api.ReadFile(f)
      for line in contents.splitlines(False):
        line = input_api.re.sub(r'//.*$', '', line)  # Strip C++ comment.
        if pattern.search(line):
          files.append(f)
          break

  if files:
    return [ output_api.PresubmitError(
        'Found Singleton<T> in the following header files.\n' +
        'Please move them to an appropriate source file so that the ' +
        'template gets instantiated in a single compilation unit.',
        files) ]
  return []


def PanProjectChecks(input_api, output_api,
                     excluded_paths=None, text_files=None,
                     license_header=None, project_name=None,
                     owners_check=True):
  """Checks that ALL chromium orbit projects should use.

  These are checks to be run on all Chromium orbit project, including:
    Chromium
    Native Client
    V8
  When you update this function, please take this broad scope into account.
  Args:
    input_api: Bag of input related interfaces.
    output_api: Bag of output related interfaces.
    excluded_paths: Don't include these paths in common checks.
    text_files: Which file are to be treated as documentation text files.
    license_header: What license header should be on files.
    project_name: What is the name of the project as it appears in the license.
  Returns:
    A list of warning or error objects.
  """
  excluded_paths = tuple(excluded_paths or [])
  text_files = tuple(text_files or (
      r'.+\.txt$',
      r'.+\.json$',
  ))
  project_name = project_name or 'Chromium'
  license_header = license_header or (
      r'.*? Copyright \(c\) %(year)s The %(project)s Authors\. '
        r'All rights reserved\.\n'
      r'.*? Use of this source code is governed by a BSD-style license that '
        r'can be\n'
      r'.*? found in the LICENSE file\.(?: \*/)?\n'
  ) % {
      'year': input_api.time.strftime('%Y'),
      'project': project_name,
  }

  results = []
  # This code loads the default black list (e.g. third_party, experimental, etc)
  # and add our black list (breakpad, skia and v8 are still not following
  # google style and are not really living this repository).
  # See presubmit_support.py InputApi.FilterSourceFile for the (simple) usage.
  black_list = input_api.DEFAULT_BLACK_LIST + excluded_paths
  white_list = input_api.DEFAULT_WHITE_LIST + text_files
  sources = lambda x: input_api.FilterSourceFile(x, black_list=black_list)
  text_files = lambda x: input_api.FilterSourceFile(
      x, black_list=black_list, white_list=white_list)

  snapshot_memory = []
  def snapshot(msg):
    """Measures & prints performance warning if a rule is running slow."""
    dt2 = input_api.time.clock()
    if snapshot_memory:
      delta_ms = int(1000*(dt2 - snapshot_memory[0]))
      if delta_ms > 500:
        print "  %s took a long time: %dms" % (snapshot_memory[1], delta_ms)
    snapshot_memory[:] = (dt2, msg)

  if owners_check:
    snapshot("checking owners")
    results.extend(input_api.canned_checks.CheckOwners(
        input_api, output_api, source_file_filter=None))

  snapshot("checking long lines")
  results.extend(input_api.canned_checks.CheckLongLines(
      input_api, output_api, source_file_filter=sources))
  snapshot( "checking tabs")
  results.extend(input_api.canned_checks.CheckChangeHasNoTabs(
      input_api, output_api, source_file_filter=sources))
  snapshot( "checking stray whitespace")
  results.extend(input_api.canned_checks.CheckChangeHasNoStrayWhitespace(
      input_api, output_api, source_file_filter=sources))
  snapshot("checking nsobjects")
  results.extend(_CheckConstNSObject(
      input_api, output_api, source_file_filter=sources))
  snapshot("checking singletons")
  results.extend(_CheckSingletonInHeaders(
      input_api, output_api, source_file_filter=sources))

  # The following checks are only done on commit, since the commit bot will
  # auto-fix most of these.
  if input_api.is_committing:
    snapshot("checking eol style")
    results.extend(input_api.canned_checks.CheckChangeSvnEolStyle(
        input_api, output_api, source_file_filter=text_files))
    snapshot("checking svn mime types")
    results.extend(input_api.canned_checks.CheckSvnForCommonMimeTypes(
        input_api, output_api))
    snapshot("checking license")
    results.extend(input_api.canned_checks.CheckLicense(
        input_api, output_api, license_header, source_file_filter=sources))
    snapshot("checking was uploaded")
    results.extend(input_api.canned_checks.CheckChangeWasUploaded(
        input_api, output_api))
  snapshot("done")
  return results
