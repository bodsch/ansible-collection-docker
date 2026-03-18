from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


@pytest.mark.parametrize("files", ["busybox-1", "hello-world-1"])
def test_properties(host, get_vars, files):
    dir = host.file(get_vars.get("container_env_directory"))

    for file in [
        f"{dir.linked_to}/{files}/{files}.properties",
    ]:
        f = host.file(file)
        assert f.is_file


def test_default_property_file(host, get_vars):
    """ """
    dir = host.file(get_vars.get("container_env_directory"))

    repl_user_key = "replicator.tmp_dir"
    repl_user_val = "var/tmp"

    property_file = host.file(f"{dir.linked_to}/busybox-1/busybox-1.properties")

    assert property_file.is_file
    assert repl_user_key in property_file.content_string
    assert repl_user_val in property_file.content_string


def test_custom_property_file(host, get_vars):
    """ """
    dir = host.file(get_vars.get("container_env_directory"))

    repl_user_key = "replicator.user"
    repl_user_val = "replicator"

    property_file = host.file(f"{dir.linked_to}/busybox-1/publisher.properties")

    assert property_file.is_file
    assert repl_user_key in property_file.content_string
    assert repl_user_val in property_file.content_string
