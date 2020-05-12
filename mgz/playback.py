"""API for recorded game playback."""

import asyncio
import logging
import os
import shutil
import struct
import time
from enum import Enum

import aiohttp
import flatbuffers
import tqdm

from AOC import ConfigMessage
from AOC import GameMessage

from mgz import fast


LOGGER = logging.getLogger(__name__)
WS_URL = 'ws://{}'
MAX_ATTEMPTS = 5
TOTAL_TIMEOUT = 60 * 4
IO_TIMEOUT = 10


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
            interval=1000, cycles=10000, total_timeout=TOTAL_TIMEOUT, io_timeout=IO_TIMEOUT
    ):
        """Async factory."""
        self = Client(playback, rec_path)
        self.start_time = start_time
        self.duration = duration
        self.total_timeout = total_timeout
        self.io_timeout = io_timeout
        self.session, self.state_ws = await self.start_instance(interval, cycles)
        LOGGER.info("launched instance for %s", rec_path)
        return self

    async def start_instance(self, interval, cycles):
        """Start headless instance and connect."""
        shutil.copyfile(
            self.rec_path,
            os.path.join(self.dropbox_path, os.path.basename(self.rec_path))
        )
        # wait for any existing AOC to be killed so we don't connect to wrong WS
        await asyncio.sleep(2)
        attempts = 0
        url = WS_URL.format(self.socket)
        LOGGER.info("trying to connect @ %s", url)
        session = aiohttp.ClientSession()
        while attempts < MAX_ATTEMPTS:
            try:
                websocket = await asyncio.wait_for(session.ws_connect(url), timeout=self.io_timeout)
                try:
                    await asyncio.wait_for(websocket.send_bytes(make_config(interval, cycles)), timeout=self.io_timeout)
                except asyncio.TimeoutError:
                    LOGGER.error("failed to send configuration")
                    break
                LOGGER.info("sent configuration to websocket")
                return session, websocket
            except (aiohttp.client_exceptions.ClientError, asyncio.TimeoutError):
                LOGGER.info("trying again to connect ...")
                await asyncio.sleep(1)
                attempts += 1
        LOGGER.error("failed to launch playback")
        self._handle.close()
        await session.close()
        raise RuntimeError("failed to launch playback")

    async def read_state(self):
        """Read memory state messages."""
        async for message in self.state_ws:
            yield read_message(message.data)

    async def sync(self):
        """Synchronize state and body messages."""
        mgz_time = self.start_time
        ws_time = 0
        mgz_done = False
        ws_done = False
        LOGGER.info("starting synchronization")
        start = time.time()
        keep_reading = True
        fast.meta(self._handle)
        while not mgz_done or not ws_done:
            if self.total_timeout and time.time() - start > self.total_timeout:
                LOGGER.warning("playback time exceeded timeout (%d%% completed)", int(mgz_time/self.duration * 100))
                break
            try:
                while not mgz_done and (mgz_time <= ws_time or ws_done):
                    op_type, payload = fast.operation(self._handle)
                    if op_type == fast.Operation.SYNC:
                        mgz_time += payload[0]
                    elif op_type == fast.Operation.CHAT and payload:
                        yield mgz_time, Source.MGZ, (op_type, payload.strip(b'\x00'))
                    elif op_type == fast.Operation.ACTION:
                        yield mgz_time, Source.MGZ, (op_type, payload)
            except EOFError:
                LOGGER.info("MGZ parsing stream finished")
                mgz_done = True
            while not ws_done and (ws_time <= mgz_time or mgz_done):
                try:
                    data = await asyncio.wait_for(self.read_state().__anext__(), timeout=self.io_timeout)
                except (asyncio.TimeoutError, asyncio.streams.IncompleteReadError):
                    LOGGER.warning("state reader timeout")
                    keep_reading = False
                    break
                ws_time = data.WorldTime()
                if data.GameFinished():
                    LOGGER.info("state reader stream finished")
                    ws_done = True
                yield ws_time, Source.MEMORY, data
            if not keep_reading:
                break
        if ws_done and mgz_done:
            LOGGER.info("synchronization finished in %.2f seconds", time.time() - start)
        else:
            raise RuntimeError("synchronization timeout encountered")
        await self.session.close()
        self._handle.close()
