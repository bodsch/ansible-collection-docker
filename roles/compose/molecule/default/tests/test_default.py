from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


@pytest.mark.parametrize("dirs",
    ["/usr/local/opt/docker-compose",],
)
def test_directories(host, dirs):

    d = host.file(dirs)
    assert d.is_directory


@pytest.mark.parametrize("files",
    ["/usr/bin/docker-compose",],
)
def test_files(host, files):

    d = host.file(files)
    assert d.is_file
