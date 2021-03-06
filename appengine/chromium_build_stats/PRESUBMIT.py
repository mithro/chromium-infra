# Copyright (c) 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Top-level presubmit script for chromium-build-stats (or go appengine app).

See http://dev.chromium.org/developers/how-tos/depottools/presubmit-scripts for
details on the presubmit API built into gcl.
"""

def reporoot(input_api):
  return input_api.os_path.join(input_api.PresubmitLocalPath(), '..', '..')

def _go_files(input_api, source_file_filter=None):
  """Collects affected go source files, but ignores ones generated by protoc."""
  files = []
  for f in input_api.AffectedTextFiles(source_file_filter):
    if not f.LocalPath().endswith('.go'):
      continue
    if f.LocalPath().endswith('.pb.go'):
      continue
    files.append(f)
  return files

def _run_go_tool(input_api, args):
  cmdline = [input_api.os_path.join(reporoot(input_api), 'appengine',
                                    'chromium_build_stats', 'goenv.sh')]
  cmdline.extend(args)
  cwd = reporoot(input_api)
  p = input_api.subprocess.Popen(cmdline,
                                 cwd=cwd,
                                 stdout=input_api.subprocess.PIPE,
                                 stderr=input_api.subprocess.STDOUT)
  (out, _) = p.communicate()
  return (out, p.returncode)

def _CheckChangeByGoTool(input_api, output_api, source_file_filter=None,
                         go_tool=None,
                         msgPrefix=None):
  """Checks that all '.go' files pass by go_tool."""
  tool = ' '.join(go_tool)
  cmdline = []
  cmdline.extend(go_tool)
  items = _go_files(input_api, source_file_filter)
  files = [f.LocalPath() for f in items]
  if not len(files):
    return []
  cmdline.extend(files)
  out, ret = _run_go_tool(input_api, cmdline)
  msg = ""
  if ret:
    msg = "Failed to run %s" % tool
  if out:
    msg = "\n".join([msg, out])
  if msg:
    return [output_api.PresubmitError(msgPrefix+"\n"+msg, items=items)]
  return []

def CheckGo(cmd, input_api, output_api, source_file_filter=None):
  """Checks that all directories test pass by goapp command."""
  items = _go_files(input_api, source_file_filter)
  dirs = set()
  for f in items:
    dirs.add(input_api.os_path.join(reporoot(input_api),
                                    input_api.os_path.dirname(f.LocalPath())))
  if not len(dirs):
    return []
  result=[]
  for d in dirs:
    cmdline = [input_api.os_path.join(reporoot(input_api), 'appengine',
                                      'chromium_build_stats', 'goenv.sh')]
    cmdline.extend(['goapp', cmd])
    p = input_api.subprocess.Popen(cmdline,
                                   cwd=d,
                                   stdout=input_api.subprocess.PIPE,
                                   stderr=input_api.subprocess.STDOUT)
    (out, _) = p.communicate()
    msg = ""
    if p.returncode:
      msg = "Failed to run goapp %s in %s" % (cmd, d)
      if out:
        msg = "\n".join([msg, out])
    if msg:
      result.append(output_api.PresubmitError(msg, items=items))
  return result


def CheckChangeGoFmtClean(input_api, output_api, source_file_filter=None):
  return _CheckChangeByGoTool(input_api, output_api,
                              source_file_filter=source_file_filter,
                              go_tool=['gofmt', '-l'],
                              msgPrefix="gofmt check")


def CommonChecks(input_api, output_api):
  results = []
  results += input_api.canned_checks.CheckChangeHasDescription(
      input_api, output_api)
  results += CheckChangeGoFmtClean(input_api, output_api)
  # disable vet due to sdk error
  # https://code.google.com/p/googleappengine/issues/detail?id=11401
  # results += CheckGo('vet', input_api, output_api)
  results += CheckGo('build', input_api, output_api)
  results += CheckGo('test', input_api, output_api)
  results += input_api.canned_checks.CheckChangeHasNoCrAndHasOnlyOneEol(
      input_api, output_api)
  # go uses TAB.
  #results += input_api.canned_checks.CheckChangeHasNoTabs(
  #   input_api, output_api)
  results += input_api.canned_checks.CheckChangeTodoHasOwner(
      input_api, output_api)
  results += input_api.canned_checks.CheckChangeHasNoStrayWhitespace(
      input_api, output_api)
  # go accepts long lines.
  #results += input_api.canned_checks.CheckLongLines(input_api, output_api, 80)
  results += input_api.canned_checks.CheckLicense(
      input_api, output_api,
      r'(Copyright 201\d Google Inc. All Rights Reserved.|' +
       'Copyright.*The Chromium Authors. All rights reserved.)')
  results += input_api.canned_checks.CheckDoNotSubmit(
      input_api, output_api)
  return results


def CheckChangeOnUpload(input_api, output_api):
  return CommonChecks(input_api, output_api)


def CheckChangeOnCommit(input_api, output_api):
  output = CommonChecks(input_api, output_api)
  output.extend(input_api.canned_checks.CheckOwners(input_api, output_api))
  return output
