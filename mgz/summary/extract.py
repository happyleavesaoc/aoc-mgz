""""Extract data via playback."""

import logging

from mgz.playback import Client, Source
from mgz.summary.chat import parse_chat


LOGGER = logging.getLogger(__name__)


def get_lobby_chat(header, encoding, diplomacy_type, players):
    """Get lobby chat."""
    chats = []
    for message in header.lobby.messages:
        if not message.message:
            continue
        try:
            chat = parse_chat(
                message.message.decode(encoding), 0, players, diplomacy_type, origination='lobby'
            )
            chats.append(chat)
        except UnicodeDecodeError:
            LOGGER.warning('could not decode lobby chat')
    return chats


async def get_extracted_data( # pylint: disable=too-many-arguments, too-many-locals
        header, encoding, diplomacy_type, players, start_time, duration, playback, handle
):
    """Get extracted data."""
    timeseries = []
    chats = get_lobby_chat(header, encoding, diplomacy_type, players)
    client = await Client.create(playback, handle.name, start_time, duration)

    async for tick, source, message in client.sync(timeout=120):
        if source == Source.MGZ and message[0] == 4:
            try:
                chats.append(parse_chat(
                    message[1].decode(encoding), tick, players, diplomacy_type
                ))
            except UnicodeDecodeError:
                LOGGER.warning('could not decode chat')

        elif source == Source.MEMORY:
            for i in range(0, message.PlayersLength()):
                player = message.Players(i)
                timeseries.append({
                    'timestamp': tick,
                    'number': player.PlayerId(),
                    'population': player.Population(),
                    'military': player.MilitaryPopulation(),
                    'percent_explored': player.PercentMapExplored(),
                    'headroom': int(player.Headroom()),
                    'food': int(player.Food()),
                    'wood': int(player.Wood()),
                    'stone': int(player.Stone()),
                    'gold': int(player.Gold())
                })

    handle.close()
    return {
        'chat': chats,
        'timeseries': timeseries
    }
