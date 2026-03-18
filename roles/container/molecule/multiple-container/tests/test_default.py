from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


def test_directory(host, get_vars):
    dir = host.file(get_vars.get("container_env_directory"))
    assert dir.exists
    assert dir.is_directory


@pytest.mark.parametrize(
    "directories",
    [
        "/tmp/busybox-1",
        "/tmp/busybox-2",
        # volumes
        "/tmp/busybox-1/nginx",
        "/tmp/busybox-1/testing3",
        "/tmp/busybox-1/testing4",
        "/tmp/busybox-1/testing6",
        # mounts
        "/tmp/busybox-1/testing1",
        "/tmp/busybox-1/testing2",
        "/opt/busybox-1/registry",
        # mounts
        "/tmp/busybox-2/testing1",
        "/tmp/busybox-2/testing2",
    ],
)
def test_volumes_directories(host, directories):
    dir = host.file(directories)
    assert dir.is_directory


@pytest.mark.parametrize(
    "files", ["busybox-2", "busybox-4", "busybox-5", "hello-world-1"]
)
def test_environments(host, get_vars, files):
    dir = host.file(get_vars.get("container_env_directory"))

    for file in [
        f"{dir.linked_to}/{files}/container.env",
    ]:
        f = host.file(file)
        assert f.is_file


@pytest.mark.parametrize("files", ["hello-world-1"])
def test_properties(host, get_vars, files):
    dir = host.file(get_vars.get("container_env_directory"))

    for file in [
        f"{dir.linked_to}/{files}/{files}.properties",
    ]:
        f = host.file(file)
        assert f.is_file
