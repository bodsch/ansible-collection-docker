from __future__ import annotations, unicode_literals

import os

import pytest
import testinfra.utils.ansible_runner
from helper.molecule import get_vars, infra_hosts, local_facts

testinfra_hosts = infra_hosts(host_name="instance")

# --- tests -----------------------------------------------------------------


def test_directories(host, get_vars):
    """ """
    root_dir = (
        get_vars.get("registry_storage", {})
        .get("filesystem", {})
        .get("rootdirectory", {})
    )

    directories = []
    directories.append(get_vars.get("registry_config_dir"))

    if root_dir:
        directories.append(root_dir)

    for dirs in directories:
        d = host.file(dirs)
        assert d.is_directory


def test_files(host, get_vars):
    """ """
    distribution = host.system_info.distribution
    release = host.system_info.release

    print(f"distribution: {distribution}")
    print(f"release     : {release}")

    _facts = local_facts(host=host, fact="registry")

    version = _facts.get("version")

    install_dir = get_vars.get("registry_install_path")
    defaults_dir = get_vars.get("registry_defaults_directory")
    config_dir = get_vars.get("registry_config_dir")

    if "latest" in install_dir:
        install_dir = install_dir.replace("latest", version)

    files = []
    files.append("/usr/bin/registry")

    if install_dir:
        files.append(f"{install_dir}/registry")
    if defaults_dir and not distribution == "artix":
        files.append(f"{defaults_dir}/registry")
    if config_dir:
        files.append(f"{config_dir}/config.yml")

    print(files)

    for _file in files:
        f = host.file(_file)
        assert f.exists
        assert f.is_file


def test_user(host, get_vars):
    """ """
    user = get_vars.get("registry_system_user", "registry")
    group = get_vars.get("registry_system_group", "registry")

    assert host.group(group).exists
    assert host.user(user).exists
    assert group in host.user(user).groups
    assert host.user(user).home == "/nonexistent"


def test_service(host, get_vars):
    service = host.service("registry")
    assert service.is_enabled
    assert service.is_running


def test_open_port(host, get_vars):
    """ """
    listen_address = "127.0.0.1:5000"

    service = host.socket(f"tcp://{listen_address}")
    assert service.is_listening
