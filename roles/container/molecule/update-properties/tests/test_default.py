from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


@pytest.mark.parametrize("files", ["hello-world"])
def test_properties(host, get_vars, files):
    dir = host.file(get_vars.get("container_env_directory"))

    for file in [
        f"{dir.linked_to}/{files}/{files}.properties",
    ]:
        f = host.file(file)
        assert f.is_file


def test_property_file(host, get_vars):
    """ """
    dir = host.file(get_vars.get("container_env_directory"))

    repl_user_key = "replicator.user"
    repl_user_val = "replicator"

    property_file = host.file(f"{dir.linked_to}/hello-world/hello-world.properties")

    assert property_file.is_file
    assert repl_user_key in property_file.content_string
    assert repl_user_val in property_file.content_string


def test_property_changes(host, get_vars):
    """ """
    import re

    dir = host.file(get_vars.get("container_env_directory"))

    property_file = host.file(f"{dir.linked_to}/hello-world/hello-world.properties")
    content = property_file.content_string.split("\n")

    re_recursion_depth = re.compile("publisher.maxRecursionDepth.*= 900")

    assert len(list(filter(re_recursion_depth.match, content))) > 0
