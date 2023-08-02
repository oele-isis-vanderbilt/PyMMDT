import pathlib
import threading
import datetime
import logging
import tempfile
from typing import Dict, Optional

from ..networking import Client
from ..states import NodeState
from ..networking.enums import GENERAL_MESSAGE, WORKER_MESSAGE, NODE_MESSAGE
from ..data_protocols import NodePubTable
from ..service import Service
from ..eventbus import EventBus, Event, TypedObserver
from .node_config import NodeConfig
from .events import (
    ProcessNodePubTableEvent,
    RegisteredMethodEvent,
    GatherEvent
)


class WorkerCommsService(Service):
    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        node_config: NodeConfig,
        worker_logdir: Optional[pathlib.Path] = None,
        logging_level: int = logging.INFO,
        worker_logging_port: int = 5555,
        state: Optional[NodeState] = None,
        logger: Optional[logging.Logger] = None,
        eventbus: Optional[EventBus] = None,
    ):
        super().__init__(name=name)

        # Obtaining worker information
        self.host = host
        self.port = port
        self.worker_logging_port = worker_logging_port
        self.logging_level = logging_level
        self.node_config = node_config
        self.logger = logger
        self.eventbus = eventbus

        if worker_logdir:
            self.worker_logdir = worker_logdir
        else:
            self.worker_logdir = pathlib.Path(tempfile.mktemp())

        # Internal state variables
        self.running: bool = False

        # If given the eventbus, add the observers
        if self.eventbus:
            self.add_observers()
    
    ####################################################################
    ## Helper Functions
    ####################################################################

    def in_node_config(self, state: NodeState, logger: logging.Logger, eventbus: EventBus):

        # Save parameters
        self.state = state
        self.logger = logger
        self.eventbus = eventbus


    def add_observers(self):
        ...

        # Add the observers

    ####################################################################
    ## Lifecycle Hooks
    ####################################################################

    async def setup(self):

        # self.logger.debug(
        #     f"{self}: Prepping the networking component of the Node, connecting to \
        #     Worker at {self.host}:{self.port}"
        # )

        # Create client to the Worker
        self.client = Client(
            host=self.host,
            port=self.port,
            id=self.state.id,
            ws_handlers={
                GENERAL_MESSAGE.SHUTDOWN: self.shutdown,
                WORKER_MESSAGE.BROADCAST_NODE_SERVER: self.process_node_pub_table,
                WORKER_MESSAGE.REQUEST_STEP: self.async_step,
                WORKER_MESSAGE.REQUEST_COLLECT: self.provide_collect,
                WORKER_MESSAGE.REQUEST_GATHER: self.provide_gather,
                WORKER_MESSAGE.START_NODES: self.start_node,
                WORKER_MESSAGE.RECORD_NODES: self.record_node,
                WORKER_MESSAGE.STOP_NODES: self.stop_node,
                WORKER_MESSAGE.REQUEST_METHOD: self.execute_registered_method,
            },
            parent_logger=self.logger,
            thread=self.eventbus.thread
        )
        await self.client.async_connect()

        # Send publisher port and host information
        await self.client.async_send(
            signal=NODE_MESSAGE.STATUS,
            data=self.state.to_dict(),
        )

    async def teardown(self):

        # Shutdown the client
        await self.client.async_shutdown()
        # self.logger.debug(f"{self}: shutdown")
    
    ####################################################################
    ## Helper Methods
    ####################################################################

    async def send_state(self):
        await self.client.async_send(
            signal=NODE_MESSAGE.STATUS, data=self.state.to_dict()
        )

    ####################################################################
    ## Message Reactivity API
    ####################################################################

    async def process_node_pub_table(self, msg: Dict):

        node_pub_table = NodePubTable.from_json(msg["data"])

        # Pass the information to the Poller Service
        event_data = ProcessNodePubTableEvent(node_pub_table)
        await self.eventbus.asend(Event('setup_connections', event_data))

        self.state.fsm = "CONNECTED"

    async def start_node(self, msg: Dict = {}):
        await self.eventbus.asend(Event("start"))
        self.state.fsm = "PREVIEWING"

    async def record_node(self, msg: Dict):
        await self.eventbus.asend(Event("record"))
        self.state.fsm = "RECORDING"
    
    async def stop_node(self, msg: Dict):
        await self.eventbus.asend(Event('stop'))
        self.state.fsm = "STOPPED"
    
    async def provide_collect(self, msg: Dict):
        await self.eventbus.asend(Event('collect'))
        self.state.fsm = "SAVED"

    async def execute_registered_method(self, msg: Dict):
        # self.logger.debug(f"{self}: execute register method: {msg}")

        # Check first that the method exists
        method_name, params = (msg["data"]["method_name"], msg["data"]["params"])

        # Send the event
        event_data = RegisteredMethodEvent(method_name=method_name, params=params, client=self.client)
        await self.eventbus.asend(Event('registered_method', event_data))

    async def async_step(self, msg: Dict):
        await self.eventbus.asend(Event('manual_step'))

    async def provide_gather(self, msg: Dict):
        event_data = GatherEvent(self.client)
        await self.eventbus.asend(Event('gather', event_data))
