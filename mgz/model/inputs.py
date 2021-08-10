from mgz.fast import Action as ActionEnum
from mgz.model.definitions import Input

class InputFactory:

    def __init__(self, gaia):
        self.gaia = gaia
        self.buildings = {}
        self.oid_cache = {}
        self.inputs = []
        self.last_vl = None
        self.prev_ts = None

    def add_chat(self, chat):
        self.inputs.append(Input(chat.timestamp, "Chat", None, dict(message=chat.message), chat.player, None))

    def add_viewlock(self, viewlock):
        pos = (viewlock.position.x, viewlock.position.y)
        if pos in self.buildings:
            n = self.buildings[pos][1]
            if n == 'Farm':
                n = 'Idle Villager'
            self.inputs.append(Input(viewlock.timestamp, f"Hotkey", n, dict(target_type=self.buildings[pos][0]), viewlock.player, viewlock.position))
        else:
            self.inputs.append(Input(viewlock.timestamp, "Viewlock", None, None, viewlock.player, viewlock.position))
        #elif pos[0] % .5 == 0 and pos[1] % .5 == 0:
        #    print(pos, 'not found')
        self.prev_ts = viewlock.timestamp

    def add_action(self, action):
        translate = {
            'DE_QUEUE': 'Queue',
            'DE_ATTACK_MOVE': 'Attack Move'
        }
        if action.type.name == 'DE_UNKNOWN_41':
            return
        name = translate.get(action.type.name, action.type.name).replace('_', ' ').title()
        modifier = None
        if 'object_ids' in action.payload and action.payload['object_ids']:
            self.oid_cache[action.type] = action.payload['object_ids']
        elif action.type in self.oid_cache:
            action.payload['object_ids'] = self.oid_cache[action.type]
        if action.type is ActionEnum.SPECIAL:
            name = action.payload['order']
        elif action.type is ActionEnum.GAME:
            name = action.payload['command']
        elif action.type is ActionEnum.STANCE:
            name = "Stance"
            modifier = f"{action.payload['stance']}"
        elif action.type is ActionEnum.FORMATION:
            name = "Formation"
            modifier = f"{action.payload['formation']}"
        elif action.type is ActionEnum.ORDER and action.payload['target_id'] in self.gaia:
            name = "Gather"
            modifier = f"{self.gaia[action.payload['target_id']]}"
        elif action.type is ActionEnum.ORDER and (action.position.x, action.position.y) in self.buildings:
            name = "Target"
            modifier = f"{self.buildings[(action.position.x, action.position.y)][1]}"
        elif action.type is ActionEnum.GATHER_POINT:
            if action.payload['target_id'] in self.gaia:
                modifier = f"{self.gaia[action.payload['target_id']]}"
            elif (action.position.x, action.position.y)  in self.buildings:
                if len(action.payload['object_ids']) == 1 and action.payload['object_ids'][0] == action.payload['target_id']:
                    name = "Spawn"
                    modifier = f"{self.buildings[(action.position.x, action.position.y)][1]}"
                else:
                    modifier = f"{self.buildings[(action.position.x, action.position.y)][1]}"
        elif action.type in (ActionEnum.BUY, ActionEnum.SELL):
            action.payload['amount'] *= 100
        elif action.type is ActionEnum.BUILD:
            if (action.position.x, action.position.y) in self.buildings:
                if self.buildings[(action.position.x, action.position.y)][1] == 'Farm' and action.payload['building'] == 'Farm':
                    name = "Reseed"
            self.buildings[(action.position.x, action.position.y)] = (action.payload['building_id'], action.payload['building'])
        self.inputs.append(Input(
            action.timestamp,
            name,
            modifier,
            action.payload,
            action.player,
            action.position
        ))
