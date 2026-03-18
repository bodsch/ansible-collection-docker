from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


def test_directories(host, get_vars):
    """ """
    docker_config = get_vars.get("docker_config")

    if docker_config.get("data_root"):
        data_root = docker_config.get("data_root")
        d = host.file(data_root)
        assert d.is_directory

        docker_directories = [
            "buildkit",
            "containers",
            "image",
            "network",
            "plugins",
            "runtimes",
            "swarm",
            "tmp",
            "trust",
            "volumes",
        ]

        if Version(docker_version) < Version("23.0.0"):
            docker_directories.append("trust")

        if Version(docker_version) > Version("29.0.0"):
            docker_directories.remove("image")

        for directory in docker_directories:
            d = host.file(os.path.join(data_root, directory))
            assert d.is_directory


def test_listening_socket(host, get_vars):
    """ """
    distribution = host.system_info.distribution
    release = host.system_info.release

    print(distribution)
    print(release)

    for i in host.socket.get_listening_sockets():
        print(i)

    docker_config = get_vars.get("docker_config")

    if docker_config.get("hosts"):

        listeners = docker_config.get("hosts")
        print(listeners)

        for socket in listeners:
            print(socket)

            if (
                distribution == "ubuntu"
                and release == "18.04"
                and socket.startswith("unix")
            ):
                continue

            socket = host.socket(socket)
            assert socket.is_listening
