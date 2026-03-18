
from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


def test_env_directory(host, get_vars):
    """ """
    dir = host.file(get_vars.get('container_env_directory'))
    assert dir.is_directory
