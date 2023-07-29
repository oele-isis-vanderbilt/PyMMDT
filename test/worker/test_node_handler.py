import asyncio

import pytest
import chimerapy.engine as cpe
from chimerapy.engine.worker.node_handler_service import NodeHandlerService
from chimerapy.engine.worker.http_server_service import HttpServerService
from chimerapy.engine.networking.async_loop_thread import AsyncLoopThread
from chimerapy.engine.eventbus import EventBus, make_evented, Event
from chimerapy.engine.states import WorkerState

from ..conftest import linux_run_only
from ..streams.data_nodes import VideoNode, AudioNode, ImageNode, TabularNode
from ..networking.test_client_server import server

logger = cpe._logger.getLogger("chimerapy-engine")
cpe.debug()


# Constants
assert server
NAME_CLASS_MAP = {
    "vn": VideoNode,
    "img_n": ImageNode,
    "tn": TabularNode,
    "an": AudioNode,
}


@pytest.fixture(scope="module")
def node_handler_setup():

    # Event Loop
    thread = AsyncLoopThread()
    thread.start()
    eventbus = EventBus(thread=thread)

    # Requirements
    state = make_evented(WorkerState(), event_bus=eventbus)
    logger = cpe._logger.getLogger("chimerapy-engine-worker")
    log_receiver = cpe._logger.get_node_id_zmq_listener()
    log_receiver.start(register_exit_handlers=True)

    # Create service
    node_handler = NodeHandlerService(
        name="node_handler",
        state=state,
        eventbus=eventbus,
        logger=logger,
        logreceiver=log_receiver,
    )

    # Necessary dependency
    http_server = HttpServerService(
        name="http_server", state=state, thread=thread, eventbus=eventbus, logger=logger
    )
    thread.exec(http_server.start()).result(timeout=10)

    yield (node_handler, http_server)

    eventbus.send(Event("shutdown"))


def test_create_service_instance(node_handler_setup):
    ...


@pytest.mark.asyncio
@pytest.mark.parametrize("context", ["multiprocessing", "threading"])
async def test_create_node(gen_node, node_handler_setup, context):
    node_handler, _ = node_handler_setup
    assert await node_handler.async_create_node(
        cpe.NodeConfig(gen_node, context=context)
    )
    assert await node_handler.async_destroy_node(gen_node.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "context_order",
    [["multiprocessing", "threading"], ["threading", "multiprocessing"]],
)
async def test_worker_create_node_different_context(
    node_handler_setup, gen_node, con_node, context_order
):
    node_handler, _ = node_handler_setup
    assert await node_handler.async_create_node(
        cpe.NodeConfig(gen_node, context=context_order[0])
    )
    assert await node_handler.async_create_node(
        cpe.NodeConfig(con_node, context=context_order[1])
    )
    assert await node_handler.async_destroy_node(gen_node.id)
    assert await node_handler.async_destroy_node(con_node.id)


@linux_run_only
@pytest.mark.asyncio
async def test_worker_create_unknown_node(node_handler_setup):

    node_handler, _ = node_handler_setup

    class UnknownNode(cpe.Node):
        def step(self):
            return 2

    node = UnknownNode(name="Unk1")
    node_id = node.id

    # Simple single node without connection
    node_config = cpe.NodeConfig(node)
    del UnknownNode

    assert await node_handler.async_create_node(node_config)
    assert await node_handler.async_destroy_node(node_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("context", ["multiprocessing", "threading"])
async def test_starting_node(node_handler_setup, gen_node, context):
    node_handler, _ = node_handler_setup

    assert await node_handler.async_create_node(
        cpe.NodeConfig(gen_node, context=context)
    )
    logger.debug("Starting")
    assert await node_handler.async_start_nodes()
    logger.debug("Started")
    # logger.debug(f"Started: {node_handler.state}")
    await asyncio.sleep(5)
    logger.debug("Stopping")
    assert await node_handler.async_stop_nodes()
    logger.debug("Stopped")
    assert await node_handler.async_destroy_node(gen_node.id)


# @pytest.mark.parametrize("context", ["multiprocessing", "threading"])
# def test_worker_data_archiving(worker, context):

#     # Just for debugging
#     # worker.delete_temp = False

#     nodes = []
#     for node_name, node_class in NAME_CLASS_MAP.items():
#         nodes.append(node_class(name=node_name))

#     # Simple single node without connection
#     futures = []
#     for node in nodes:
#         futures.append(worker.create_node(cpe.NodeConfig(node, context=context)))

#     assert wait(futures, timeout=10)

#     logger.debug("Start nodes!")
#     worker.start_nodes().result(timeout=5)
#     logger.debug("Let nodes run for some time")
#     time.sleep(1)

#     logger.debug("Recording nodes!")
#     worker.record_nodes().result(timeout=5)
#     logger.debug("Let nodes run for some time")
#     time.sleep(1)

#     worker.stop_nodes().result(timeout=5)

#     worker.collect().result(timeout=30)

#     for node_name in NAME_CLASS_MAP:
#         assert (worker.tempfolder / node_name).exists()
