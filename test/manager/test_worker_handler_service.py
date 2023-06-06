import asyncio

import pytest

import chimerapy as cp

from ..conftest import TEST_DATA_DIR, GenNode, ConsumeNode
from .dev_manager_services_group import DevManagerServicesGroup

logger = cp._logger.getLogger("chimerapy")
cp.debug()


@pytest.mark.asyncio
@pytest.fixture
async def testbed_setup(worker):

    # Create the service
    manager_services_group = DevManagerServicesGroup(
        logdir=TEST_DATA_DIR, publisher_port=0
    )

    assert worker.connect(
        method="ip",
        host=manager_services_group.http_server.ip,
        port=manager_services_group.http_server.port,
    )

    # Define graph
    gen_node = GenNode(name="Gen1")
    con_node = ConsumeNode(name="Con1")
    simple_graph = cp.Graph()
    simple_graph.add_nodes_from([gen_node, con_node])
    simple_graph.add_edge(src=gen_node, dst=con_node)

    # Register graph
    manager_services_group.worker_handler._register_graph(simple_graph)

    yield (manager_services_group.worker_handler, worker, gen_node, con_node)

    await manager_services_group.async_apply("shutdown")


@pytest.mark.asyncio
async def test_worker_handler_create_node(testbed_setup):

    item = await testbed_setup.__anext__()
    worker_handler, worker, gen_node, con_node = item

    assert await worker_handler._request_node_creation(
        worker_id=worker.id, node_id=gen_node.id
    )

    assert await worker_handler._request_node_destruction(
        worker_id=worker.id, node_id=gen_node.id
    )


@pytest.mark.asyncio
async def test_worker_handler_create_connections(testbed_setup):

    item = await testbed_setup.__anext__()
    worker_handler, worker, gen_node, con_node = item

    # Create Nodes
    assert await worker_handler._request_node_creation(
        worker_id=worker.id, node_id=gen_node.id
    )
    assert await worker_handler._request_node_creation(
        worker_id=worker.id, node_id=con_node.id
    )

    # Get the node information
    await worker_handler._request_node_server_data(worker_id=worker.id)
    assert worker_handler.nodes_server_table != {}

    # Create connections
    assert await worker_handler._request_connection_creation(worker_id=worker.id)

    # Teardown
    assert await worker_handler.reset()


@pytest.mark.asyncio
async def test_worker_handler_lifecycle_graph(testbed_setup):

    item = await testbed_setup.__anext__()
    worker_handler, worker, gen_node, con_node = item

    assert await worker_handler.commit(
        graph=worker_handler.graph, mapping={worker.id: [gen_node.id, con_node.id]}
    )
    assert await worker_handler.start_workers()

    await asyncio.sleep(5)

    assert await worker_handler.stop()
    assert await worker_handler.collect()

    # Teardown
    assert await worker_handler.reset()