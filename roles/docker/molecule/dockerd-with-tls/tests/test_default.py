
from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------



def test_packages(host):
    """
    """
    distribution = host.system_info.distribution
    release = host.system_info.release

    print(distribution)
    print(release)

    packages = []
    packages.append("iptables")

    if not distribution == "artix":
        if distribution == 'arch':
            packages.append("docker")
        else:
            packages.append("docker-ce")

        for package in packages:
            p = host.package(package)
            assert p.is_installed


@pytest.mark.parametrize("dirs", [
    "/etc/docker",
])
def test_directories(host, dirs):

    d = host.file(dirs)
    assert d.is_directory
    assert d.exists


def test_service_running_and_enabled(host):

    service = host.service('docker')
    assert service.is_running
    assert service.is_enabled
