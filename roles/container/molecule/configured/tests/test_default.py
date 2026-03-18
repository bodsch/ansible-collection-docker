from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


def test_env_directory(host, get_vars):
    dir = host.file(get_vars.get("container_env_directory"))
    assert dir.is_directory


@pytest.mark.parametrize(
    "directories",
    [
        "/tmp/testing1",
        "/tmp/testing2",
        "/tmp/testing3",
        "/tmp/testing4",
        "/tmp/testing6",
    ],
)
def test_volumes_directories(host, directories):
    dir = host.file(directories)
    assert dir.is_directory


@pytest.mark.parametrize(
    "directories",
    [
        "/tmp/testing5",
    ],
)
def test_volume_directory(host, directories):
    dir = host.file(directories)
    assert not dir.is_directory


@pytest.mark.parametrize(
    "directories",
    [
        "/tmp/testing1",
        "/opt/registry",
    ],
)
def test_mountpoint_directories(host, directories):
    dir = host.file(directories)
    assert dir.is_directory


@pytest.mark.parametrize("files", ["hello-world"])
def test_environments(host, get_vars, files):
    dir = host.file(get_vars.get("container_env_directory"))

    for file in [
        f"{dir.linked_to}/{files}/container.env",
    ]:
        f = host.file(file)
        assert f.is_file


@pytest.mark.parametrize("files", ["hello-world"])
def test_properties(host, get_vars, files):
    dir = host.file(get_vars.get("container_env_directory"))

    for file in [
        f"{dir.linked_to}/{files}/{files}.properties",
    ]:
        f = host.file(file)
        assert f.is_file


@pytest.mark.parametrize(
    "files",
    [
        "/usr/local/bin/list_all_container.sh",
        "/usr/local/bin/list_all_images.sh",
        "/usr/local/bin/parse_container_fact.sh",
        "/usr/local/bin/prune.sh",
        "/usr/local/bin/remove_stopped_container.sh",
        "/usr/local/bin/remove_untagged_images.sh",
    ],
)
def test_pre_and_post_task_files(host, get_vars, files):
    f = host.file(files)
    assert f.is_file


def test_environment_file(host, get_vars):
    """ """
    dir = host.file(get_vars.get("container_env_directory"))

    virtual_host = "hello-world.local"

    environment_file = host.file(f"{dir.linked_to}/hello-world/container.env")

    assert environment_file.is_file
    assert virtual_host in environment_file.content_string


def test_property_file(host, get_vars):
    """ """
    dir = host.file(get_vars.get("container_env_directory"))

    repl_user_key = "replicator.user"
    repl_user_val = "replicator"

    property_file = host.file(f"{dir.linked_to}/hello-world/hello-world.properties")

    assert property_file.is_file
    assert repl_user_key in property_file.content_string
    assert repl_user_val in property_file.content_string
