
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
    """
    """
    cwd = os.getcwd()

    if 'group_vars' in os.listdir(cwd):
        directory = "../.."
        molecule_directory = "."
    else:
        directory = "."
        molecule_directory = f"molecule/{os.environ.get('MOLECULE_SCENARIO_NAME')}"

    return directory, molecule_directory


def read_ansible_yaml(file_name, role_name):
    """
    """
    read_file = None

    for e in ["yml", "yaml"]:
        test_file = "{}.{}".format(file_name, e)
        if os.path.isfile(test_file):
            read_file = test_file
            break

    return f"file={read_file} name={role_name}"


@pytest.fixture()
def get_vars(host):
    """
        parse ansible variables
        - defaults/main.yml
        - vars/main.yml
        - vars/${DISTRIBUTION}.yaml
        - molecule/${MOLECULE_SCENARIO_NAME}/group_vars/all/vars.yml
    """
    base_dir, molecule_dir = base_directory()
    distribution = host.system_info.distribution
    operation_system = None

    if distribution in ['debian', 'ubuntu']:
        operation_system = "debian"
    elif distribution in ['redhat', 'ol', 'centos', 'rocky', 'almalinux']:
        operation_system = "redhat"
    elif distribution in ['arch', 'artix']:
        operation_system = f"{distribution}linux"

    # print(" -> {} / {}".format(distribution, os))
    # print(" -> {}".format(base_dir))

    file_defaults      = read_ansible_yaml(f"{base_dir}/defaults/main", "role_defaults")
    file_vars          = read_ansible_yaml(f"{base_dir}/vars/main", "role_vars")
    file_distibution   = read_ansible_yaml(f"{base_dir}/vars/{operation_system}", "role_distibution")
    file_molecule      = read_ansible_yaml(f"{molecule_dir}/group_vars/all/vars", "test_vars")
    # file_host_molecule = read_ansible_yaml("{}/host_vars/{}/vars".format(base_dir, HOST), "host_vars")

    defaults_vars      = host.ansible("include_vars", file_defaults).get("ansible_facts").get("role_defaults")
    vars_vars          = host.ansible("include_vars", file_vars).get("ansible_facts").get("role_vars")
    distibution_vars   = host.ansible("include_vars", file_distibution).get("ansible_facts").get("role_distibution")
    molecule_vars      = host.ansible("include_vars", file_molecule).get("ansible_facts").get("test_vars")
    # host_vars          = host.ansible("include_vars", file_host_molecule).get("ansible_facts").get("host_vars")

    ansible_vars = defaults_vars
    ansible_vars.update(vars_vars)
    ansible_vars.update(distibution_vars)
    ansible_vars.update(molecule_vars)
    # ansible_vars.update(host_vars)

    templar = Templar(loader=DataLoader(), variables=ansible_vars)
    result = templar.template(ansible_vars, fail_on_undefined=False)

    return result


def test_env_directory(host, get_vars):
    dir = host.file(get_vars.get('container_env_directory'))
    assert dir.exists
    assert dir.is_directory


@pytest.mark.parametrize("directories", [
    "/tmp/testing1",
    "/tmp/testing2",
    "/tmp/testing3",
    "/tmp/testing4",
    "/tmp/testing6",
])
def test_volumes_directories(host, directories):
    dir = host.file(directories)
    assert dir.is_directory


@pytest.mark.parametrize("directories", [
    "/tmp/testing5",
])
def test_volume_directory(host, directories):
    dir = host.file(directories)
    assert not dir.is_directory


@pytest.mark.parametrize("directories", [
    "/tmp/testing1",
    "/opt/registry",
])
def test_mountpoint_directories(host, directories):
    dir = host.file(directories)
    assert dir.is_directory


@pytest.mark.parametrize("files", [
    "hello-world"
])
def test_environments(host, get_vars, files):
    dir = host.file(get_vars.get('container_env_directory'))

    for file in [
        f"{dir.linked_to}/{files}/container.env",
    ]:
        f = host.file(file)
        assert f.is_file


@pytest.mark.parametrize("files", [
    "hello-world"
])
def test_properties(host, get_vars, files):
    dir = host.file(get_vars.get('container_env_directory'))

    for file in [
        f"{dir.linked_to}/{files}/{files}.properties",
    ]:
        f = host.file(file)
        assert f.is_file


@pytest.mark.parametrize("files", [
    "/usr/local/bin/list_all_container.sh",
    "/usr/local/bin/list_all_images.sh",
    "/usr/local/bin/parse_container_fact.sh",
    "/usr/local/bin/prune.sh",
    "/usr/local/bin/remove_stopped_container.sh",
    "/usr/local/bin/remove_untagged_images.sh",
])
def test_pre_and_post_task_files(host, get_vars, files):
    f = host.file(files)
    assert f.is_file


def test_environment_file(host, get_vars):
    """
    """
    dir = host.file(get_vars.get('container_env_directory'))

    virtual_host = "hello-world.local"

    environment_file = host.file(f"{dir.linked_to}/hello-world/container.env")

    assert environment_file.is_file
    assert virtual_host in environment_file.content_string


def test_property_file(host, get_vars):
    """
    """
    dir = host.file(get_vars.get('container_env_directory'))

    repl_user_key = "replicator.user"
    repl_user_val = "replicator"

    property_file = host.file(f"{dir.linked_to}/hello-world/hello-world.properties")

    assert property_file.is_file
    assert repl_user_key in property_file.content_string
    assert repl_user_val in property_file.content_string
