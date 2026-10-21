from __future__ import annotations

import asyncio
import logging

from .common import DeskError

LOG = logging.getLogger(__name__)


class Hub:
    def __init__(self, auth, max_clients=3):
        self.auth, self.max_clients = auth, max_clients
        self.connections = {}

    async def join(self, socket, token):
        self.auth.check(token)
        if len(self.connections) >= self.max_clients:
            raise DeskError("too_many_clients", "已达到同时连接数量上限", 429)
        self.connections[socket] = token

    def leave(self, socket):
        self.connections.pop(socket, None)

    async def send(self, socket, data):
        try:
            self.auth.check(self.connections[socket])
            await asyncio.wait_for(socket.send_json(data), timeout=2)
        except DeskError:
            self.leave(socket)
            await socket.close(code=1008)
        except Exception:
            self.leave(socket)

    async def broadcast(self, data):
        if self.connections:
            await asyncio.gather(*(self.send(socket, data) for socket in list(self.connections)), return_exceptions=True)

    async def close(self):
        for socket in list(self.connections):
            try:
                await socket.close(code=1001)
            except Exception:
                pass
        self.connections.clear()
