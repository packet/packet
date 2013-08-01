# Copyright (c) 2012 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Defines class Rietveld to easily access a rietveld instance.

Security implications:

The following hypothesis are made:
- Rietveld enforces:
  - Nobody else than issue owner can upload a patch set
  - Verifies the issue owner credentials when creating new issues
  - A issue owner can't change once the issue is created
  - A patch set cannot be modified
"""

import logging
import os
import re
import sys
import time
import urllib2

try:
  import simplejson as json  # pylint: disable=F0401
except ImportError:
  try:
    import json  # pylint: disable=F0401
  except ImportError:
    # Import the one included in depot_tools.
    sys.path.append(os.path.join(os.path.dirname(__file__), 'third_party'))
    import simplejson as json  # pylint: disable=F0401

#from third_party import upload
import patch

# Hack out upload logging.info()
upload.logging = logging.getLogger('upload')
# Mac pylint choke on this line.
upload.logging.setLevel(logging.WARNING)  # pylint: disable=E1103


class Rietveld(object):
  """Accesses rietveld."""
  def __init__(self, url, email, password, extra_headers=None):
    self.url = url.rstrip('/')
    # TODO(maruel): It's not awesome but maybe necessary to retrieve the value.
    # It happens when the presubmit check is ran out of process, the cookie
    # needed to be recreated from the credentials. Instead, it should pass the
    # email and the cookie.
    self.email = email
    self.password = password
    if email and password:
      get_creds = lambda: (email, password)
      self.rpc_server = upload.HttpRpcServer(
            self.url,
            get_creds,
            extra_headers=extra_headers or {})
    else:
      self.rpc_server = upload.GetRpcServer(url, email)
    self._xsrf_token = None
    self._xsrf_token_time = None

  def xsrf_token(self):
    if (not self._xsrf_token_time or
        (time.time() - self._xsrf_token_time) > 30*60):
      self._xsrf_token_time = time.time()
      self._xsrf_token = self.get(
          '/xsrf_token',
          extra_headers={'X-Requesting-XSRF-Token': '1'})
    return self._xsrf_token

  def get_pending_issues(self):
    """Returns an array of dict of all the pending issues on the server."""
    return json.loads(self.get(
        '/search?format=json&commit=2&closed=3&keys_only=True&limit=1000')
        )['results']

  def close_issue(self, issue):
    """Closes the Rietveld issue for this changelist."""
    logging.info('closing issue %s' % issue)
    self.post("/%d/close" % issue, [('xsrf_token', self.xsrf_token())])

  def get_description(self, issue):
    """Returns the issue's description."""
    return self.get('/%d/description' % issue)

  def get_issue_properties(self, issue, messages):
    """Returns all the issue's metadata as a dictionary."""
    url = '/api/%s' % issue
    if messages:
      url += '?messages=true'
    return json.loads(self.get(url))

  def get_patchset_properties(self, issue, patchset):
    """Returns the patchset properties."""
    url = '/api/%s/%s' % (issue, patchset)
    return json.loads(self.get(url))

  def get_file_content(self, issue, patchset, item):
    """Returns the content of a new file.

    Throws HTTP 302 exception if the file doesn't exist or is not a binary file.
    """
    # content = 0 is the old file, 1 is the new file.
    content = 1
    url = '/%s/image/%s/%s/%s' % (issue, patchset, item, content)
    return self.get(url)

  def get_file_diff(self, issue, patchset, item):
    """Returns the diff of the file.

    Returns a useless diff for binary files.
    """
    url = '/download/issue%s_%s_%s.diff' % (issue, patchset, item)
    return self.get(url)

  def get_patch(self, issue, patchset):
    """Returns a PatchSet object containing the details to apply this patch."""
    props = self.get_patchset_properties(issue, patchset) or {}
    out = []
    for filename, state in props.get('files', {}).iteritems():
      logging.debug('%s' % filename)
      status = state.get('status')
      if not status:
        raise patch.UnsupportedPatchFormat(
            filename, 'File\'s status is None, patchset upload is incomplete.')
      if status[0] not in ('A', 'D', 'M'):
        raise patch.UnsupportedPatchFormat(
            filename, 'Change with status \'%s\' is not supported.' % status)

      svn_props = self.parse_svn_properties(
          state.get('property_changes', ''), filename)

      if state.get('is_binary'):
        if status[0] == 'D':
          if status[0] != status.strip():
            raise patch.UnsupportedPatchFormat(
                filename, 'Deleted file shouldn\'t have property change.')
          out.append(patch.FilePatchDelete(filename, state['is_binary']))
        else:
          out.append(patch.FilePatchBinary(
              filename,
              self.get_file_content(issue, patchset, state['id']),
              svn_props,
              is_new=(status[0] == 'A')))
        continue

      try:
        diff = self.get_file_diff(issue, patchset, state['id'])
      except urllib2.HTTPError, e:
        if e.code == 404:
          raise patch.UnsupportedPatchFormat(
              filename, 'File doesn\'t have a diff.')
        raise

      # FilePatchDiff() will detect file deletion automatically.
      p = patch.FilePatchDiff(filename, diff, svn_props)
      out.append(p)
      if status[0] == 'A':
        # It won't be set for empty file.
        p.is_new = True
      if (len(status) > 1 and
          status[1] == '+' and
          not (p.source_filename or p.svn_properties)):
        raise patch.UnsupportedPatchFormat(
            filename, 'Failed to process the svn properties')

    return patch.PatchSet(out)

  @staticmethod
  def parse_svn_properties(rietveld_svn_props, filename):
    """Returns a list of tuple [('property', 'newvalue')].

    rietveld_svn_props is the exact format from 'svn diff'.
    """
    rietveld_svn_props = rietveld_svn_props.splitlines()
    svn_props = []
    if not rietveld_svn_props:
      return svn_props
    # 1. Ignore svn:mergeinfo.
    # 2. Accept svn:eol-style and svn:executable.
    # 3. Refuse any other.
    # \n
    # Added: svn:ignore\n
    #    + LF\n

    spacer = rietveld_svn_props.pop(0)
    if spacer or not rietveld_svn_props:
      # svn diff always put a spacer between the unified diff and property
      # diff
      raise patch.UnsupportedPatchFormat(
          filename, 'Failed to parse svn properties.')

    while rietveld_svn_props:
      # Something like 'Added: svn:eol-style'. Note the action is localized.
      # *sigh*.
      action = rietveld_svn_props.pop(0)
      match = re.match(r'^(\w+): (.+)$', action)
      if not match or not rietveld_svn_props:
        raise patch.UnsupportedPatchFormat(
            filename,
            'Failed to parse svn properties: %s, %s' % (action, svn_props))

      if match.group(2) == 'svn:mergeinfo':
        # Silently ignore the content.
        rietveld_svn_props.pop(0)
        continue

      if match.group(1) not in ('Added', 'Modified'):
        # Will fail for our French friends.
        raise patch.UnsupportedPatchFormat(
            filename, 'Unsupported svn property operation.')

      if match.group(2) in ('svn:eol-style', 'svn:executable', 'svn:mime-type'):
        # '   + foo' where foo is the new value. That's fragile.
        content = rietveld_svn_props.pop(0)
        match2 = re.match(r'^   \+ (.*)$', content)
        if not match2:
          raise patch.UnsupportedPatchFormat(
              filename, 'Unsupported svn property format.')
        svn_props.append((match.group(2), match2.group(1)))
    return svn_props

  def update_description(self, issue, description):
    """Sets the description for an issue on Rietveld."""
    logging.info('new description for issue %s' % issue)
    self.post('/%s/description' % issue, [
        ('description', description),
        ('xsrf_token', self.xsrf_token())])

  def add_comment(self, issue, message):
    logging.info('issue %s; comment: %s' % (issue, message))
    return self.post('/%s/publish' % issue, [
        ('xsrf_token', self.xsrf_token()),
        ('message', message),
        ('message_only', 'True'),
        ('send_mail', 'True'),
        ('no_redirect', 'True')])

  def set_flag(self, issue, patchset, flag, value):
    return self.post('/%s/edit_flags' % issue, [
        ('last_patchset', str(patchset)),
        ('xsrf_token', self.xsrf_token()),
        (flag, value)])

  def search(
      self,
      owner=None, reviewer=None,
      base=None,
      closed=None, private=None, commit=None,
      created_before=None, created_after=None,
      modified_before=None, modified_after=None,
      per_request=None, keys_only=False,
      with_messages=False):
    """Yields search results."""
    # These are expected to be strings.
    string_keys = {
        'owner': owner,
        'reviewer': reviewer,
        'base': base,
        'created_before': created_before,
        'created_after': created_after,
        'modified_before': modified_before,
        'modified_after': modified_after,
    }
    # These are either None, False or True.
    three_state_keys = {
      'closed': closed,
      'private': private,
      'commit': commit,
    }

    url = '/search?format=json'
    # Sort the keys mainly to ease testing.
    for key in sorted(string_keys):
      value = string_keys[key]
      if value:
        url += '&%s=%s' % (key, urllib2.quote(value))
    for key in sorted(three_state_keys):
      value = three_state_keys[key]
      if value is not None:
        url += '&%s=%d' % (key, int(value) + 1)

    if keys_only:
      url += '&keys_only=True'
    if with_messages:
      url += '&with_messages=True'
    if per_request:
      url += '&limit=%d' % per_request

    cursor = ''
    while True:
      output = self.get(url + cursor)
      if output.startswith('<'):
        # It's an error message. Return as no result.
        break
      data = json.loads(output) or {}
      if not data.get('results'):
        break
      for i in data['results']:
        yield i
      cursor = '&cursor=%s' % data['cursor']

  def get(self, request_path, **kwargs):
    kwargs.setdefault('payload', None)
    return self._send(request_path, **kwargs)

  def post(self, request_path, data, **kwargs):
    ctype, body = upload.EncodeMultipartFormData(data, [])
    return self._send(request_path, payload=body, content_type=ctype, **kwargs)

  def _send(self, request_path, **kwargs):
    """Sends a POST/GET to Rietveld.  Returns the response body."""
    try:
      # Sadly, upload.py calls ErrorExit() which does a sys.exit(1) on HTTP
      # 500 in AbstractRpcServer.Send().
      old_error_exit = upload.ErrorExit
      def trap_http_500(msg):
        """Converts an incorrect ErrorExit() call into a HTTPError exception."""
        m = re.search(r'(50\d) Server Error', msg)
        if m:
          # Fake an HTTPError exception. Cheezy. :(
          raise urllib2.HTTPError(request_path, m.group(1), msg, None, None)
        old_error_exit(msg)
      upload.ErrorExit = trap_http_500

      maxtries = 5
      for retry in xrange(maxtries):
        try:
          logging.debug('%s' % request_path)
          result = self.rpc_server.Send(request_path, **kwargs)
          # Sometimes GAE returns a HTTP 200 but with HTTP 500 as the content.
          # How nice.
          return result
        except urllib2.HTTPError, e:
          if retry >= (maxtries - 1):
            raise
          if e.code not in (500, 502, 503):
            raise
        except urllib2.URLError, e:
          if retry >= (maxtries - 1):
            raise
          if not 'Name or service not known' in e.reason:
            # Usually internal GAE flakiness.
            raise
        # If reaching this line, loop again. Uses a small backoff.
        time.sleep(1+maxtries*2)
    finally:
      upload.ErrorExit = old_error_exit

  # DEPRECATED.
  Send = get
