# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
import os
import sys
import subprocess

VERSION_PATH = 'mantidimaging/versions.py'

git_describe = subprocess.check_output(['git', 'describe', '--long', '--abbrev=40'], encoding='utf8')
if git_describe.count('-') != 2:
    raise ValueError(f"Could not parse git describe output: {git_describe}")

tag, commit_count, git_hash = git_describe.strip().split("-")

package_version = tag
if commit_count:
    package_version += f".post{commit_count}"
git_hash = git_hash[1:]

package_type = ''
if "CONDA_BUILD" in os.environ:
    package_type = 'conda'
    package_version = os.environ['PKG_VERSION']

output_source = f"""# This file is automatically generated by {sys.argv[0]}

package_version = '{package_version}'
git_hash = '{git_hash}'
package_type = '{package_type}'
"""

with open(VERSION_PATH, 'w') as fh:
    fh.write(output_source)
