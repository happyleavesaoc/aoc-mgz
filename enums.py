from construct import Enum, Pass

def ObjectEnum(ctx):
	# Should export the whole list from the game for the best accuracy
	return Enum(ctx,
		villager_male = 83,
		villager_female = 293,
		scout_cavalry = 448,
		eagle_warrior = 751,
		king = 434,
		flare = 332,
		relic = 285,
		turkey = 833,
		sheep = 594,
		deer = 65,
		boar = 48,
		javelina = 822,
		wolf = 126,
		jaguar = 812,
		hawk = 96,
		macaw = 816,
		shore_fish = 69,
		fish_1 = 455,
		fish_2 = 456,
		fish_4 = 458,
		fish_3 = 457,
		marlin_1 = 450,
		dolphin_1 = 451,
		cactus = 709,
		berry_bush = 59,
		stone_pile = 102,
		gold_pile = 66,
		forest_tree = 350,
		forest_tree_2 = 411,
		snow_pine_tree = 413,
		straggler_tree = 349,
		tc_1 = 109,
		tc_2 = 618,
		tc_3 = 619,
		tc_4 = 620,
		castle = 70,
		palisade_wall = 72,
		stone_wall = 117,
		stone_gate_1 = 64,
		stone_gate_2 = 81,
		stone_gate_3 = 88,
		stone_gate_4 = 95,
		fortified_wall = 155,
		cliff_1 = 264,
		cliff_2 = 265,
		cliff_3 = 266,
		cliff_4 = 267,
		cliff_5 = 268,
		cliff_6 = 269,
		cliff_7 = 270,
		cliff_8 = 271,
		cliff_9 = 272,
		cliff_10 = 273,
		outpost = 598,
		shipwreck = 722,
		map_revealer = 837,
		_default_ = Pass
	)

"""Buildings: action context"""
def BuildingEnum(ctx):
	return Enum(ctx,
		dock = 45,
		tc = 621,
		_default_ = Pass
	)

def GameTypeEnum(ctx):
	return Enum(ctx,
		RM = 0,
		Regicide = 1,
		DM = 2
	)

def ObjectTypeEnum(ctx):
	return Enum(ctx,
		gaia = 10,
		other = 20,
		doppelganger = 25,
		fish = 30,
		bird = 40,
		projectile = 60,
		unit = 70,
		building = 80,
		_default_ = Pass
	)

def PlayerTypeEnum(ctx):
	return Enum(ctx,
		invalid = 0,
		unknown = 1,
		human = 2,
		computer = 4
	)

def DifficultyEnum(ctx):
	return Enum(ctx,
		hardest = 0,
		hard = 1,
		standard = 2,
		easy = 3,
		easiest = 4
	)

def GameSpeedEnum(ctx):
	return Enum(ctx,
		slow = 100,
		standard = 150,
		fast = 200,
	)

def OperationEnum(ctx):
	return Enum(ctx,
		action = 1,
		sync = 2,
		message = 4,
		_default_ = "savedchapter"
	)

def MessageEnum(ctx):
	return Enum(ctx,
		start = 500,
		_default_ = "chat"
	)

def ResourceEnum(ctx):
	return Enum(ctx,
		food = 0,
		wood = 1,
		stone = 2,
		gold = 3,
		decay = 12,
		fish = 17,
		_default_ = Pass # lots of resource types exist
	)

def VictoryEnum(ctx):
	return Enum(ctx,
		standard = 0,
		conquest = 1,
		time_limit = 7,
		score = 8,
		last_man = 11
	)

def ResourceLevelEnum(ctx):
	return Enum(ctx,
		none = -1,
		standard = 0,
		low = 1,
		medium = 2,
		high = 3
	)

def RevealMapEnum(ctx):
	return Enum(ctx,
		normal = 0,
		explored = 1,
		all_visible = 2
	)

def StartingAgeEnum(ctx):
	return Enum(ctx,
		unset = -1,
		dark = 0,
		feudal = 1,
		castle = 2,
		imperial = 3,
		post_imperial = 4
	)

def TheirDiplomacyEnum(ctx):
	return Enum(ctx,
		ally_or_self = 0,
		enemy = 3
	)

def MyDiplomacyEnum(ctx):
	return Enum(ctx,
		gaia = 0,
		self = 1,
		ally = 2,
		neutral = 3,
		enemy = 4,
		invalid_player = -1
	)

def ActionEnum(ctx):
	return Enum(ctx,
		attack = 0,
		stop = 1,
		move = 3,
		resign = 11,
		waypoint = 16,
		stance = 18,
		guard = 19,
		follow = 20,
		patrol = 21,
		formation = 23,
		multiplayersave = 24,
		#unknown1 = 27,
		savedchapter = 32,
		aitrain = 100,
		research = 101,
		build = 102,
		gamespeed = 103,
		wall = 105,
		delete = 106,
		attackground = 107,
		tribute = 108,
		#unknown2 = 110,
		unload = 111,
		#unknown3 = 112,
		#unknown4 = 114,
		flare = 115,
		garrison = 117,
		train = 119,
		gatherpoint = 120,
		sell = 122,
		buy = 123,
		#unknown5 = 126,
		townbell = 127,
		backtowork = 128,
		postgame = 255,
		_default_ = Pass
	)