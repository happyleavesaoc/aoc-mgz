"""API for recorded game playback."""

import asyncio
import logging
import os
import shutil
import struct
import time
from enum import Enum

import flatbuffers
import tqdm
import websockets
from construct.core import ConstructError

from AOC import ConfigMessage
from AOC import GameMessage

from mgz import fast


LOGGER = logging.getLogger(__name__)
WS_URL = 'ws://{}'


class Source(Enum):
    """Message source."""
    MGZ = 0
    MEMORY = 1


def make_config(interval=1000, cycles=1):
    """Make a configuration flatbuffer."""
    builder = flatbuffers.Builder(64)
    ConfigMessage.ConfigMessageStart(builder)
    ConfigMessage.ConfigMessageAddMessageIntervalMs(builder, interval)
    ConfigMessage.ConfigMessageAddUpdateCycles(builder, cycles)
    builder.Finish(ConfigMessage.ConfigMessageEnd(builder))
    return bytes(builder.Output())


def read_message(buf):
    """Read a message from flatbuffer as a dict."""
    return GameMessage.GameMessage.GetRootAsGameMessage(buf, 0)


async def progress_bar(generator, duration):
    """Apply a progress bar - visualize progress in console."""
    config = {
        'total': duration,
        'unit': ' ticks',
        'miniters': int(duration/10000),
        'mininterval': 1
    }
    with tqdm.tqdm(**config) as bar_:
        last = 0
        async for tick, source, data in generator:
            increment = tick - last
            if increment > 0:
                bar_.update(increment)
                last = tick
            yield tick, source, data


class Client():
    """Represents a client instance."""

    def __init__(self, playback, rec_path):
        """Initialize."""
        parts = playback.split(':')
        self.socket = ':'.join(parts[0:-1])
        self.dropbox_path = os.path.abspath(os.path.expanduser(parts[-1]))
        self.rec_path = os.path.abspath(os.path.expanduser(rec_path))
        self._handle = open(self.rec_path, 'rb')
        header_len, _ = struct.unpack('<II', self._handle.read(8))
        self._handle.read(header_len - 8)

    # pylint: disable=attribute-defined-outside-init, too-many-arguments
    @classmethod
    async def create(
            cls, playback, rec_path, start_time, duration,
            interval=2000, cycles=10000
    ):
        """Async factory."""
        self = Client(playback, rec_path)
        self.start_time = start_time
        self.duration = duration
        self.state_ws = await self.start_instance(interval, cycles)
        LOGGER.info("launched instance for %s", rec_path)
        return self

    async def start_instance(self, interval, cycles):
        """Start headless instance and connect."""
        shutil.copyfile(
            self.rec_path,
            os.path.join(self.dropbox_path, os.path.basename(self.rec_path))
        )
        # wait for any existing AOC to be killed so we don't connect to wrong WS
        await asyncio.sleep(1)
        while True:
            try:
                url = WS_URL.format(self.socket)
                LOGGER.info("trying to connect @ %s", url)
                websocket = await websockets.connect(url, ping_timeout=None)
                await websocket.send(make_config(interval, cycles))
                LOGGER.info("sent configuration to websocket")
                return websocket
            except (
                    ConnectionRefusedError, OSError,
                    websockets.exceptions.ConnectionClosed, websockets.exceptions.InvalidMessage
                ):
                await asyncio.sleep(1)

    async def read_state(self):
        """Read memory state messages."""
        async for message in self.state_ws:
            yield read_message(message)

    async def sync(self, timeout=None):
        """Synchronize state and body messages."""
        mgz_time = self.start_time
        ws_time = 0
        mgz_done = False
        ws_done = False
        LOGGER.info("starting synchronization")
        start = time.time()
        while not mgz_done or not ws_done:
            if timeout and time.time() - start > timeout:
                LOGGER.warning("synchronization timeout encountered")
                self.close_all()
                raise RuntimeError("synchronization timeout encountered")
            try:
                while not mgz_done and (mgz_time <= ws_time or ws_done):
                    op_type, payload = fast.operation(self._handle)
                    if op_type == fast.Operation.SYNC:
                        mgz_time += payload[0]
                    elif op_type == fast.Operation.CHAT and payload:
                        yield mgz_time, Source.MGZ, (op_type, payload.strip(b'\x00'))
            except (ConstructError, ValueError, EOFError):
                LOGGER.info("MGZ parsing stream finished")
                mgz_done = True
            while not ws_done and (ws_time <= mgz_time or mgz_done):
                try:
                    data = await asyncio.wait_for(self.read_state().__anext__(), timeout=timeout)
                except (asyncio.TimeoutError, asyncio.streams.IncompleteReadError):
                    LOGGER.warning("socket timeout or read failure encountered")
                    self.close_all()
                    raise RuntimeError("socket timeout or read failure encountered")
                ws_time = data.WorldTime()
                if data.GameFinished():
                    LOGGER.info("state reader stream finished")
                    ws_done = True
                yield ws_time, Source.MEMORY, data
        LOGGER.info("synchronization finished in %.2f seconds", time.time() - start)
        self.close_all()

    def close_all(self):
        """Close websocket."""
        try:
            asyncio.ensure_future(self.state_ws.close())
        except websockets.exceptions.ConnectionClosed:
            pass
        self._handle.close()
