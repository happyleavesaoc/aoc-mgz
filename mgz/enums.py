"""Enumerations."""

from construct import Enum, Pass

# pylint: disable=invalid-name


def ObjectEnum(ctx):
    """Object Enumeration.

    Should export the whole list from the game for the best accuracy.
    """
    return Enum(
        ctx,
        villager_male=83,
        villager_female=293,
        scout_cavalry=448,
        eagle_warrior=751,
        king=434,
        flare=332,
        relic=285,
        turkey=833,
        sheep=594,
        deer=65,
        boar=48,
        iron_boar=810,
        ostrich=1026,
        javelina=822,
        crocodile=1031,
        rhinoceros=1139,
        wolf=126,
        jaguar=812,
        hawk=96,
        macaw=816,
        shore_fish=69,
        fish_1=455,
        fish_2=456,
        fish_4=458,
        fish_3=457,
        marlin_1=450,
        marlin_2=451,
        dolphin=452,
        cactus=709,
        berry_bush=59,
        stone_pile=102,
        gold_pile=66,
        forest_tree=350,
        forest_tree_2=411,
        snow_pine_tree=413,
        straggler_tree=349,
        tc_1=109,
        tc_2=618,
        tc_3=619,
        tc_4=620,
        castle=70,
        palisade_wall=72,
        stone_wall=117,
        stone_gate_1=64,
        stone_gate_2=81,
        stone_gate_3=88,
        stone_gate_4=95,
        palisade_gate_1=662,
        palisade_gate_2=666,
        palisade_gate_3=670,
        palisade_gate_4=674,
        fortified_wall=155,
        cliff_1=264,
        cliff_2=265,
        cliff_3=266,
        cliff_4=267,
        cliff_5=268,
        cliff_6=269,
        cliff_7=270,
        cliff_8=271,
        cliff_9=272,
        cliff_10=273,
        outpost=598,
        shipwreck=722,
        map_revealer=837,
        default=Pass
    )

def BuildingEnum(ctx):
    """Buildings Enumeration (in Action context)."""
    return Enum(
        ctx,
        dock=45,
        tc=621,
        default=Pass
    )

def GameTypeEnum(ctx):
    """Game Type Enumeration."""
    return Enum(
        ctx,
        RM=0,
        Regicide=1,
        DM=2,
        Scenario=3,
        Campaign=4,
        KingOfTheHill=5,
        WonderRace=6,
        DefendTheWonder=7,
        TurboRandom=8,
        CaptureTheRelic=10,
        SuddenDeath=11,
        BattleRoyale=12,
        EmpireWars=13
    )

def ObjectTypeEnum(ctx):
    """Object Type Enumeration."""
    return Enum(
        ctx,
        static=10,
        animated=20,
        doppelganger=25,
        moving=30,
        action=40,
        base=50,
        missile=60,
        combat=70,
        building=80,
        tree=90,
        default=Pass
    )

def PlayerTypeEnum(ctx):
    """Player Type Enumeration."""
    return Enum(
        ctx,
        absent=0,
        closed=1,
        human=2,
        eliminated=3,
        computer=4,
        cyborg=5,
        spectator=6
    )

def DifficultyEnum(ctx):
    """Difficulty Enumeration."""
    return Enum(
        ctx,
        hardest=0,
        hard=1,
        moderate=2,
        standard=3,
        easiest=4,
        extreme=5,
        unknown=6
    )

def OperationEnum(ctx):
    """Operation Enumeration."""
    return Enum(
        ctx,
        action=1,
        sync=2,
        viewlock=3,
        chat=4,
        default="embedded"
    )

def ResourceEnum(ctx):
    """Resource Type Enumeration."""
    return Enum(
        ctx,
        food=0,
        wood=1,
        stone=2,
        gold=3,
        decay=12,
        fish=17,
        default=Pass # lots of resource types exist
    )

def VictoryEnum(ctx):
    """Victory Type Enumeration."""
    return Enum(
        ctx,
        standard=0,
        conquest=1,
        exploration=2,
        ruins=3,
        artifacts=4,
        discoveries=5,
        gold=6,
        time_limit=7,
        score=8,
        standard2=9,
        regicide=10,
        last_man=11
    )

def ResourceLevelEnum(ctx):
    """Resource Level Enumeration."""
    return Enum(
        ctx,
        none=-1,
        standard=0,
        low=1,
        medium=2,
        high=3,
        unknown1=4,
        unknown2=5,
        unknown3=6
    )

def RevealMapEnum(ctx):
    """Reveal Map Enumeration."""
    return Enum(
        ctx,
        normal=0,
        explored=1,
        all_visible=2,
        no_fog=3,
    )

def AgeEnum(ctx):
    """Age Enumeration."""
    return Enum(
        ctx,
        what=-2,
        unset=-1,
        dark=0,
        feudal=1,
        castle=2,
        imperial=3,
        postimperial=4,
        dmpostimperial=6,
        default='unknown'
    )

def TheirDiplomacyEnum(ctx):
    """Other Player's Diplomacy Enumeration."""
    return Enum(
        ctx,
        ally_or_self=0,
        enemy=3,
        treaty=4
    )

def DiplomacyStanceEnum(ctx):
    """Diplomacy stance."""
    return Enum(
        ctx,
        allied=0,
        neutral=1,
        enemy=3
    )

def GameActionModeEnum(ctx):
    """Game Action Modes."""
    return Enum(
        ctx,
        diplomacy=0,
        speed=1,
        instant_build=2,
        quick_build=4,
        allied_victory=5,
        cheat=6,
        unk0=9,
        spy=10,
        unk1=11,
        farm_queue=13,
        farm_unqueue=14,
        farm_autoqueue=16,
        fishtrap_queue=17,
        fishtrap_unqueue=18,
        fishtrap_autoqueue=19,
        default_stance=20,
        default=Pass
    )

def OrderTypeEnum(ctx):
    """Types of Orders."""
    return Enum(
        ctx,
        packtreb=1,
        unpacktreb=2,
        garrison=5,
        default=Pass
    )

def ReleaseTypeEnum(ctx):
    """Types of Releases."""
    return Enum(
        ctx,
        all=0,
        selected=3,
        sametype=4,
        notselected=5,
        inversetype=6,
        default=Pass
    )

def StanceEnum(ctx):
    """Types of stances."""
    return Enum(
        ctx,
        aggressive=0,
        defensive=1,
        stand_ground=2,
        passive=3
    )

def FormationEnum(ctx):
    """Types of formations."""
    return Enum(
        ctx,
        line=2,
        box=4,
        staggered=7,
        flank=8
    )

def MyDiplomacyEnum(ctx):
    """Player's Diplomacy Enumeration."""
    return Enum(
        ctx,
        gaia=0,
        self=1,
        ally=2,
        neutral=3,
        enemy=4,
        invalid_player=-1
    )

def ActionEnum(ctx):
    """Action Enumeration."""
    return Enum(
        ctx,
        interact=0,
        stop=1,
        ai_interact=2,
        move=3,
        create=4,
        add_attribute=5,
        give_attribute=6,
        ai_move=10,
        resign=11,
        spec=15,
        waypoint=16,
        stance=18,
        guard=19,
        follow=20,
        patrol=21,
        formation=23,
        save=27,
        ai_waypoint=31,
        chapter=32,
        de_unknown_35=35,
        de_unknown_37=37,
        de_attackmove=33,
        de_autoscout=38,
        de_unknown_39=39,
        ai_command=53,
        ai_queue=100,
        research=101,
        build=102,
        game=103,
        wall=105,
        delete=106,
        attackground=107,
        tribute=108,
        de_unknown_109=109,
        repair=110,
        release=111,
        multiqueue=112,
        togglegate=114,
        flare=115,
        order=117,
        queue=119,
        gatherpoint=120,
        sell=122,
        buy=123,
        droprelic=126,
        townbell=127,
        backtowork=128,
        de_queue=129,
        de_unknown_130=130,
        de_unknown_131=131,
        de_unknown_135=135,
        de_unknown_196=196,
        postgame=255,
        default=Pass
    )
