import sys
import pathlib
import os
import pdb

import pytest
from pytest_lazyfixture import lazy_fixture
import chimerapy as cp

cp.debug()

# Internal Imports
from .conftest import linux_run_only

# Constant
TEST_DIR = pathlib.Path(os.path.abspath(__file__)).parent
TEST_PACKAGE_DIR = TEST_DIR / "mock"


@pytest.fixture
def local_node_graph(gen_node):
    graph = cp.Graph()
    graph.add_node(gen_node)
    return graph


@pytest.fixture
def packaged_node_graph():
    # Installing test package (in case this test package hasn't been done before
    # Reference: https://stackoverflow.com/a/55188705/13231446
    try:
        import test_package as tp
    except ImportError:
        import pip._internal as pip

        pip.main(["install", str(TEST_PACKAGE_DIR)])
    finally:
        import test_package as tp

    node = tp.TestNode(name="test")
    graph = cp.Graph()
    graph.add_node(node)
    return graph


@linux_run_only
@pytest.mark.parametrize(
    "config_graph",
    [
        (lazy_fixture("local_node_graph")),
        (lazy_fixture("packaged_node_graph")),
    ],
)
def test_sending_package(manager, dockered_worker, config_graph):
    dockered_worker.connect(host=manager.host, port=manager.port)

    manager.commit_graph(
        graph=config_graph,
        mapping={dockered_worker.name: list(config_graph.G.nodes())},
        timeout=10,
        send_packages=[
            {"name": "test_package", "path": TEST_PACKAGE_DIR / "test_package"}
        ],
    )

    for node_name in config_graph.G.nodes():
        assert (
            manager.workers[dockered_worker.name]["nodes_status"][node_name]["INIT"]
            == 1
        )