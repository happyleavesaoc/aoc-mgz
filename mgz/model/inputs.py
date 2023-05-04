"""Refine player actions into inputs."""

from mgz.fast import Action as ActionEnum
from mgz.model.definitions import Input


ACTION_TRANSLATE = {
    ActionEnum.DE_QUEUE: 'Queue',
    ActionEnum.DE_ATTACK_MOVE: 'Attack Move'
}


class Inputs:
    """Normalize player inputs."""

    def __init__(self, gaia):
        """Initialize."""
        self._gaia = gaia
        self._buildings = {}
        self._oid_cache = {}
        self.inputs = []

    def add_chat(self, chat):
        """Add chat input."""
        self.inputs.append(Input(chat.timestamp, 'Chat', None, dict(message=chat.message), chat.player, None))

    def add_action(self, action):
        """Add action input."""
        if action.type in (ActionEnum.DE_TRANSFORM, ActionEnum.POSTGAME):
            return
        name = ACTION_TRANSLATE.get(action.type, action.type.name).replace('_', ' ').title()
        param = None
        if 'object_ids' in action.payload and action.payload['object_ids']:
            self._oid_cache[action.type] = action.payload['object_ids']
        elif action.type in self._oid_cache:
            action.payload['object_ids'] = self._oid_cache[action.type]
        if action.type is ActionEnum.SPECIAL:
            name = action.payload['order']
        elif action.type is ActionEnum.GAME:
            name = action.payload['command']
            if name == 'Speed':
                param = action.payload['speed']
        elif action.type is ActionEnum.STANCE:
            name = 'Stance'
            param = action.payload['stance']
        elif action.type is ActionEnum.FORMATION:
            name = 'Formation'
            param = action.payload['formation']
        elif action.type is ActionEnum.ORDER and action.payload['target_id'] in self._gaia:
            name = 'Gather'
            param = self._gaia[action.payload['target_id']]
        elif action.type is ActionEnum.ORDER and action.position and action.position.hash() in self._buildings:
            name = 'Target'
            param = self._buildings[action.position.hash()]
        elif action.type is ActionEnum.GATHER_POINT:
            if action.payload['target_id'] in self._gaia:
                param = self._gaia[action.payload['target_id']]
            elif action.position and action.position.hash() in self._buildings:
                if len(action.payload['object_ids']) == 1 and action.payload['object_ids'][0] == action.payload['target_id']:
                    name = 'Spawn'
                param = self._buildings[action.position.hash()]
        elif action.type in (ActionEnum.BUY, ActionEnum.SELL):
            action.payload['amount'] *= 100
        elif action.type is ActionEnum.BUILD:
            param = action.payload['building']
            if action.position.hash() in self._buildings:
                if self._buildings[action.position.hash()] == 'Farm' and action.payload['building'] == 'Farm':
                    name = 'Reseed'
            self._buildings[action.position.hash()] = action.payload['building']
        elif action.type in (ActionEnum.QUEUE, ActionEnum.DE_QUEUE):
            param = action.payload['unit']
        elif action.type is ActionEnum.RESEARCH:
            param = action.payload['technology']
        new_input = Input(
            action.timestamp,
            name,
            param,
            action.payload,
            action.player,
            action.position
        )
        self.inputs.append(new_input)
        return new_input
