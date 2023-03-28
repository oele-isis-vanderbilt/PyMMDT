from typing import List
import datetime
import traceback
from concurrent.futures import Future

from aiohttp import web

from chimerapy import config
from .manager import Manager
from .networking.enums import MANAGER_MESSAGE
from . import _logger

logger = _logger.getLogger("chimerapy")


class API:
    def __init__(self, manager: Manager):
        self.manager = manager
        self.manager.server.add_routes(
            [
                web.get("/network", self.get_network),
                web.post("/start", self.post_start),
                web.post("/stop", self.post_stop),
                web.post("/collect", self.post_collect),
            ]
        )
        self.futures: List[Future] = []

    ####################################################################
    # Helper Functions
    ####################################################################

    def future_flush(self):

        for future in self.futures:
            try:
                future.result(timeout=config.get("manager.timeout.info-request"))
            except Exception as e:
                logger.error(traceback.format_exc())

    ####################################################################
    # HTTP Routes
    ####################################################################

    async def get_network(self, request: web.Request):
        return web.json_response(self.manager.state.to_dict())

    async def post_stop(self, request: web.Request):

        # Mark the stop time
        self.manager.stop_time = datetime.datetime.now()
        self.manager.duration = (
            self.manager.stop_time - self.manager.start_time
        ).total_seconds()

        # Request stop from all Workers
        success = await self.manager.async_broadcast_request(
            htype="post", route="/nodes/stop"
        )

        if success:
            self.manager.state.running = False
            return web.HTTPOk()
        else:
            return web.HTTPError()

    async def post_start(self, request: web.Request):

        # Mark the start time
        self.manager.start_time = datetime.datetime.now()

        # Request start from all Workers
        success = await self.manager.async_broadcast_request(
            htype="post", route="/nodes/start"
        )
        logger.debug(success)

        if success:
            self.manager.state.running = True
            return web.HTTPOk()
        else:
            return web.HTTPError()

    async def post_collect(self, request: web.Request):

        # First, request Nodes to save their data
        if self.manager.state.collecting:
            return web.HTTPOk()
        else:
            self.manager.state.collecting = True

            success = await self.manager.async_broadcast_request(
                htype="post", route="/nodes/save"
            )
            logger.debug(success)

            if success:
                future = self.manager.server._thread.exec(self.manager.async_collect())
                self.futures.append(future)
                return web.HTTPOk()
            else:
                return web.HTTPError()

    ####################################################################
    # WS
    ####################################################################

    async def broadcast_state_update(self):
        await self.manager.server.async_broadcast(
            signal=MANAGER_MESSAGE.NODE_STATUS_UPDATE,
            data=self.manager.state.to_dict(),
        )
