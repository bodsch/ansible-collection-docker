
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar
import pytest
import os
import testinfra.utils.ansible_runner

import pprint
pp = pprint.PrettyPrinter()

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def base_directory():
    cwd = os.getcwd()

    if ('group_vars' in os.listdir(cwd)):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = "molecule/{}".format(os.environ.get('MOLECULE_SCENARIO_NAME'))

    return directory, molecule_directory


@pytest.fixture()
def get_vars(host):
    """

    """
    base_dir, molecule_dir = base_directory()

    file_defaults = "file={}/defaults/main.yml name=role_defaults".format(base_dir)
    file_vars = "file={}/vars/main.yml name=role_vars".format(base_dir)
    file_molecule = "file={}/group_vars/all/vars.yml name=test_vars".format(molecule_dir)

    defaults_vars = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    molecule_vars = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(molecule_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_directory(host, get_vars):
    dir = host.file(get_vars.get('container_env_directory'))
    assert dir.exists
    assert dir.is_directory


@pytest.mark.parametrize("directories", [
    "/tmp/busybox-2",
    # mounts
    "/tmp/busybox-2/testing1",
    "/tmp/busybox-2/testing2",
])
def test_volumes_directories(host, directories):
    dir = host.file(directories)
    assert dir.is_directory


@pytest.mark.parametrize("directories", [
    "/tmp/busybox-1",
    # volumes
    "/tmp/busybox-1/nginx",
    "/tmp/busybox-1/testing3",
    "/tmp/busybox-1/testing4",
    "/tmp/busybox-1/testing6",
    # mounts
    "/tmp/busybox-1/testing1",
    "/tmp/busybox-1/testing2",
    "/opt/busybox-1/registry",
])
def test_no_volumes_directories(host, directories):
    dir = host.file(directories)
    assert not dir.is_directory


@pytest.mark.parametrize("files", [
    "busybox-2",
])
def test_environments(host, get_vars, files):
    dir = host.file(get_vars.get('container_env_directory'))

    for file in [
        f"{dir.linked_to}/{files}/container.env",
    ]:
        f = host.file(file)
        assert f.is_file


@pytest.mark.parametrize("files", [
    "busybox-2"
])
def test_properties(host, get_vars, files):
    dir = host.file(get_vars.get('container_env_directory'))

    for file in [
        f"{dir.linked_to}/{files}/{files}.properties",
    ]:
        f = host.file(file)
        assert f.is_file
