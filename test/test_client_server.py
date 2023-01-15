from typing import Dict
import time
import socket
import logging
import pathlib
import os
import platform
import tempfile
import uuid
from aiohttp import web
import requests

from concurrent.futures import wait, Future

import pytest
from pytest_lazyfixture import lazy_fixture
import numpy as np

import pdb

import chimerapy as cp

logger = cp._logger.getLogger("chimerapy")
cp.debug()

# Constants
TEST_DIR = pathlib.Path(os.path.abspath(__file__)).parent
IMG_SIZE = 400


async def hello(request):
    return web.Response(text="Hello, world")


async def echo(msg: Dict, ws: web.WebSocketResponse = None):
    logger.debug("ECHO: " + str(msg))


@pytest.fixture
def server():
    server = cp.Server(
        name="test", port=8080, routes=[web.get("/", hello)], ws_handlers={-11111: echo}
    )
    server.serve()
    yield server
    server.shutdown()


@pytest.fixture
def client(server):
    client = cp.Client(
        name="test",
        host=server.host,
        port=server.port,
        ws_handlers={-11111: echo},
    )
    client.connect()
    yield client
    client.shutdown()


def test_server_http_req_res(server):
    r = requests.get(f"http://{server.host}:{server.port}")
    assert r.status_code == 200 and r.text == "Hello, world"


def test_server_websocket_connection(server, client):
    assert client.name in list(server.ws_clients.keys())


def test_server_send_to_client(server, client):
    # Simple send
    server.send(client_name=client.name, signal=-11111, data="HELLO")

    # Simple send with OK
    server.send(client_name=client.name, signal=-11111, data="HELLO", ok=True)

    cp.utils.waiting_for(
        lambda: client.msg_processed_counter >= 2,
        timeout=2,
        timeout_msg=f"{client}: Didn't receive the necessary 2 messages.",
    )


def test_client_send_to_server(server, client):
    # Simple send
    client.send(signal=-11111, data="HELLO")

    # Simple send with OK
    client.send(signal=-11111, data="HELLO", ok=True)

    cp.utils.waiting_for(
        lambda: server.msg_processed_counter >= 2,
        timeout=2,
        timeout_msg=f"{server}: Didn't receive the necessary 2 messages.",
    )


def test_multiple_clients_send_to_server(server):

    clients = []
    for i in range(5):
        client = cp.Client(
            host=server.host,
            port=server.port,
            name=f"test-{i}",
            ws_handlers={"echo": echo},
        )
        clients.append(client)

    futures = []
    for client in clients:
        futures.append(client.send({"signal": "echo", "data": "ECHO!"}, ack=True))

    wait(futures)
    for client in clients:
        client.send({"signal": "echo", "data": "ECHO!"}, ack=True)

    for client in clients:
        client.shutdown()


def test_server_broadcast_to_multiple_clients(server):

    clients = []
    for i in range(5):
        client = cp.Client(
            host=server.host,
            port=server.port,
            name=f"test-{i}",
            ws_handlers={"echo": echo, "SHUTDOWN": echo},
        )
        client.start()
        clients.append(client)

    # Wait until all clients are connected
    while len(server.client_comms) <= 4:
        time.sleep(0.1)

    futures = server.broadcast({"signal": "echo", "data": "ECHO!"}, ack=True)
    wait(futures)

    for client in clients:
        client.shutdown()


# @pytest.mark.repeat(10)
@pytest.mark.parametrize(
    "dir",
    [
        (TEST_DIR / "mock" / "data" / "simple_folder"),
        (TEST_DIR / "mock" / "data" / "chimerapy_logs"),
    ],
)
def test_client_sending_folder_to_server(server, client, dir):

    # Action
    client.send_folder(name="test", folderpath=dir)

    # Get the expected behavior
    miss_counter = 0
    while len(server.file_transfer_records.keys()) == 0:

        miss_counter += 1
        time.sleep(0.1)

        if miss_counter > 100:
            assert False, "File transfer failed after 10 second"


@pytest.mark.parametrize(
    "dir",
    [
        (TEST_DIR / "mock" / "data" / "simple_folder"),
        (TEST_DIR / "mock" / "data" / "chimerapy_logs"),
    ],
)
def test_server_broadcast_file_to_clients(server, dir):

    clients = []
    for i in range(5):
        client = cp.Client(
            host=server.host,
            port=server.port,
            name=f"test-{i}",
            connect_timeout=2,
            sender_msg_type=cp.WORKER_MESSAGE,
            accepted_msg_type=cp.MANAGER_MESSAGE,
            handlers={"echo": echo, "SHUTDOWN": echo},
        )
        client.start()
        clients.append(client)

    # Wait until all clients are connected
    while len(server.client_comms) <= 4:
        time.sleep(0.1)

    # Broadcast file
    server.send_folder(name="test", folderpath=dir)

    # Check all clients files
    for client in clients:
        miss_counter = 0
        while len(client.file_transfer_records.keys()) == 0:

            miss_counter += 1
            time.sleep(0.1)

            if miss_counter > 100:
                assert False, "File transfer failed after 10 second"

    for client in clients:
        client.shutdown()
