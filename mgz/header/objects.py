"""Objects."""

from construct import (Array, Byte, Embedded, Flag, Float32l, If, Int16sl, Int16ub,
                       Int16ul, Int32ub, Int32ul, Padding, Peek, Struct, Int32sl,
                       Switch, Pass, RepeatUntil, Bytes, LazyBound, IfThenElse)

from mgz.enums import ObjectEnum, ObjectTypeEnum, ResourceEnum
from mgz.util import Find, Version, find_version, find_save_version, find_type
from mgz.header.unit_type import unit_type
from mgz.header.de import de_string

# pylint: disable=invalid-name


active_sprite = "active_sprite"/Struct(
    "id"/Int16ul,
    "x"/Int32ul,
    "y"/Int32ul,
    "frame"/Int16ul,
    "invisible"/Byte
)

animated_sprite = "animated_sprite"/Struct(
    "animate_interval"/Float32l,
    "animate_last"/Int32ul,
    "last_frame"/Int16ul,
    "frame_changed"/Byte,
    "frame_looped"/Byte,
    "animate_flag"/Byte,
    "last_speed"/Float32l
)

sprite_list = "sprite_list"/Struct(
    "type"/Byte,
    "active"/If(lambda ctx: ctx.type != 0, active_sprite),
    "animated"/If(lambda ctx: ctx.type == 2, animated_sprite),
    Embedded(If(lambda ctx: ctx.type != 0, Struct(
        "order"/Byte,
        "flag"/Byte,
        "count"/Byte
    )))
)

particle = "particle"/Struct(
    "type"/Int16ul,
    Embedded(If(lambda ctx: ctx.type == 1, Struct(
        "name"/de_string,
        "x"/Float32l,
        "y"/Float32l,
        Bytes(26)
    ))),
)


static = "static"/Struct(
    "object_type"/Int16ul,
    "sprite"/Int16ul,
    "garrisoned_in_id"/Int32sl,
    "hitpoints"/Float32l,
    "object_state"/Byte,
    "sleep"/Flag,
    "doppleganger"/Flag,
    "go_to_sleep"/Flag,
    "object_id"/Int32ul,
    "facet"/Byte,
    "x"/Float32l,
    "y"/Float32l,
    "z"/Float32l,
    "screen_offset_x"/Int16ul,
    "screen_offset_y"/Int16ul,
    "shadow_offset_x"/Int16ul,
    "shadow_offset_y"/Int16ul,
    "selected_group"/If(lambda ctx: find_version(ctx) == Version.AOK, Byte),
    ResourceEnum("resource_type"/Int16sl),
    "amount"/Float32l,
    "worker_count"/IfThenElse(lambda ctx: find_save_version(ctx) == 12.36, Int32ul, Byte),
    "current_damage"/Byte,
    "damaged_lately_timer"/Byte,
    "under_attack"/Byte,
    If(lambda ctx: find_save_version(ctx) < 37, Struct(
        "pathing_group_len"/Int32ul,
        "pathing_group"/Array(lambda ctx: ctx.pathing_group_len, "object_id"/Int32ul)
    )),
    If(lambda ctx: find_save_version(ctx) >= 66.3, Bytes(2)),
    "group_id"/Int32sl,
    "roo_already_called"/Byte,
    "de_static_unk1"/If(lambda ctx: find_version(ctx) == Version.DE, Bytes(17)),
    If(lambda ctx: find_save_version(ctx) >= 26.16, Byte),
    "de_has_object_props"/If(lambda ctx: find_version(ctx) == Version.DE, Int16ul),
    "de_object_props"/IfThenElse(lambda ctx: ctx.de_has_object_props == 1, Struct(
        Bytes(162),
        Find(b'`\n\x00\x00`\n\x00\x00', 1000), # Skip a large unparseable block that (likely) contains RMS-modified object data
        Bytes(2)
    ), Struct(
        "has_sprite_list"/Byte,
        "sprite_list"/If(lambda ctx: ctx.has_sprite_list != 0, RepeatUntil(lambda x,lst,ctx: lst[-1].type == 0, sprite_list)),
        "de_extension"/If(lambda ctx: find_version(ctx) == Version.DE, Struct(
            "particles"/Array(5, particle),
            If(lambda ctx: find_save_version(ctx) >= 13.15, Bytes(5)),
            If(lambda ctx: find_save_version(ctx) >= 13.17, Bytes(2)),
            If(lambda ctx: find_save_version(ctx) >= 13.34, Struct(
                Bytes(2),
                de_string,
                de_string,
                Bytes(2)
            ))
        ))
    )),
    "de_extension_p2"/If(lambda ctx: find_version(ctx) == Version.DE, Struct(
        # not the right way to do this, needs improvement
        If(lambda ctx: find_save_version(ctx) >= 20.16, Struct(
            "peek"/Peek(Bytes(6)),
            If(lambda ctx: find_save_version(ctx) >= 25.22 and (find_type(ctx) == 10 or find_save_version(ctx) >= 63.0), Bytes(1)),
            If(lambda ctx: find_save_version(ctx) >= 64.3, Bytes(1)),
            If(lambda ctx: find_save_version(ctx) < 25.22 and find_type(ctx) == 10 and ctx.peek[0] == 0 and ctx.peek[0:2] != b"\x00\x0b", Bytes(1)),
            If(lambda ctx: find_type(ctx) == 20 and ctx.peek[4] == 0 and ctx.peek[4:6] != b"\x00\x0b", Bytes(1)),
        )),
        If(lambda ctx: find_save_version(ctx) >= 61.5, Bytes(14)),
        If(lambda ctx: find_save_version(ctx) >= 62.0, Bytes(4))
    )),
    "hd_extension"/If(lambda ctx: find_version(ctx) == Version.HD and find_save_version(ctx) > 12.36, Struct(
        "flag"/Flag,
        Padding(4),
        "has_array"/Int16ul,
        "array"/If(lambda ctx: ctx.has_array, Struct(
            "values"/RepeatUntil(lambda x,lst,ctx: lst[-1].type == 0, Struct(
                "type"/Byte,
                If(lambda ctx: ctx.type > 0, Bytes(16))
            ))
        ))
    )),
    If(lambda ctx: find_save_version(ctx) >= 66.3, Bytes(4)),
)


animated = "animated"/Struct(
    Embedded(static),
    "turn_speed"/Float32l
)

path_data = "path_data"/Struct(
    "id"/Int32ul,
    "linked_path_type"/Int32ul,
    "waypoint_level"/Int32ul,
    "path_id"/Int32ul,
    "waypoint"/Int32ul,
    "state"/Int32sl,
    "range"/Float32l,
    "target_id"/Int32sl,
    "pause_time"/Float32l,
    "continue_counter"/Int32ul,
    "flags"/Int32ul,
    "hd"/If(lambda ctx: find_version(ctx) == Version.HD, Int32ul)
)

vector = Struct(
    "x"/Float32l,
    "y"/Float32l,
    "z"/Float32l
)


movement_data = "movement"/Struct(
    "velocity"/vector,
    "acceleration"/vector
)

base_moving = "base_moving"/Struct(
    Embedded(animated),
    "trail_remainder"/Int32ul,
    "velocity"/vector,
    "de_move_byte"/If(lambda ctx: find_save_version(ctx) >= 20.16, Byte),
    "angle"/Float32l,
    "turn_towards_time"/Int32ul,
    If(lambda ctx: find_save_version(ctx) < 37, Struct(
        "turn_timer"/Int32ul,
        "continue_counter"/Int32ul,
        "current_terrain_exception_1"/Int32sl,
        "current_terrain_exception_2"/Int32sl,
    )),
    "waiting_to_move"/Byte,
    "wait_delays_count"/Byte,
    "on_ground"/Byte,
    "num_path_data"/Int32ul,
    "path_data"/Array(lambda ctx: ctx.num_path_data, path_data),
    "has_future_path_data"/Int32ul,
    "future_path_data"/If(lambda ctx: ctx.has_future_path_data > 0, path_data),
    "has_movement_data"/Int32ul,
    "movement_data"/If(lambda ctx: ctx.has_movement_data > 0, movement_data),
    "de_moving_unk"/If(lambda ctx: find_version(ctx) == Version.DE and find_save_version(ctx) < 13.2, Int16ul),
    "position"/vector,
    "orientation_forward"/vector,
    "orientation_right"/vector,
    "last_move_time"/Int32ul,
    "num_user_defined_waypoints"/Int32ul,
    "user_defined_waypoints"/Array(lambda ctx: ctx.num_user_defined_waypoints, vector),
    "has_substitute_position"/Int32ul,
    "substitute_position"/vector,
    "consecutive_substitute_count"/Int32ul
)

moving = "moving"/Struct(
    Embedded(base_moving),
    "hd_moving"/If(lambda ctx: find_version(ctx) == Version.HD, Bytes(1)),
    "de_moving"/If(lambda ctx: find_version(ctx) == Version.DE, Bytes(17)),
    "ver2616"/If(lambda ctx: 37 > find_save_version(ctx) >= 26.16, Bytes(8)),
    "ver37"/If(lambda ctx: 63 > find_save_version(ctx) >= 37, Bytes(5)),
    "ver63"/If(lambda ctx: find_save_version(ctx) >= 63, Bytes(4))
)

move_to = "move_to"/Struct(
    "range"/Float32l
)

enter = "enter"/Struct(
    "first_time"/Int32ul
)

make = "make"/Struct(
    "work_timer"/Float32l
)

attack = "attack"/Struct(
    "range"/Float32l,
    "min_range"/Float32l,
    "missile_id"/Int16ul,
    "frame_delay"/Int16ul,
    "need_to_attack"/Int16ul,
    "was_same_owner"/Int16ul,
    "indirect_fire_flag"/Byte,
    "move_sprite_id"/Int16ul,
    "fight_sprite_id"/Int16ul,
    "wait_sprite_id"/Int16ul,
    "last_target_position"/vector
)

unit_action = Struct(
    "type"/Int16ul,
    "data"/If(lambda ctx: ctx.type > 0, Struct(
        "state"/IfThenElse(lambda ctx: find_version(ctx) in [Version.AOK, Version.AOC, Version.HD], Byte, Int32ul),
        "target_object_pointer"/Int32sl,
        "target_object_pointer2"/Int32sl,
        "target_object_id"/Int32sl,
        "target_object_id_2"/Int32sl,
        "position"/vector,
        "timer"/Float32l,
        "target_moved_state"/Byte,
        "task_id"/Int16ul,
        "sub_action_value"/Byte,
        "sub_actions"/LazyBound(lambda x: action_list),
        "sprite_id"/Int16sl,
        Embedded("additional"/Switch(lambda ctx: ctx._.type, {
            1: move_to,
            3: enter,
            9: attack,
            21: make
        }, default=Pass))
    ))
)

action_list = "action_list"/Struct(
    "actions"/RepeatUntil(lambda x,lst,ctx: lst[-1].type == 0, unit_action)
)

action = "action"/Struct(
    Embedded(base_moving),
    "hd_action"/If(lambda ctx: find_version(ctx) == Version.HD, Bytes(3)),
    "waiting"/Byte,
    "command_flag"/Byte,
    "selected_group_info"/If(lambda ctx: find_version(ctx) != Version.AOK, Int16ul),
    "actions"/action_list
)

base_combat = "base_combat"/Struct(
    Embedded(action),
    "formation_id"/Byte,
    "formation_row"/Byte,
    "formation_col"/Byte,
    "attack_timer"/Float32l,
    "capture_flag"/Byte,
    "multi_unified_points"/Byte,
    "large_object_radius"/Byte,
    "attack_count"/Int32ul
)

missile = "missile"/Struct(
    Embedded(base_combat),
    "max_range"/Float32l,
    "fired_from_id"/Int32ul,
    "own_base"/Byte,
    "base"/If(lambda ctx: ctx.own_base > 0, unit_type),
    If(lambda ctx: find_save_version(ctx) >= 26.16, Bytes(34))
)

waypoint = "waypoint"/Struct(
    vector,
    "facet_to_next_waypoint"/Byte,
    Padding(3)
)

gatherpoint = "gatherpoint"/Struct(
    "exists"/Int32ul,
    "position"/vector,
    "object_id"/Int32sl,
    "unit_type_id"/Int16sl
)

path = "path"/Struct(
)

order = "order"/Struct(
    "issuer"/Int32ul,
    "type"/Int32ul,
    "priority"/Int32ul,
    "target_id"/Int32ul,
    "target_player"/Int32ul,
    "target_location"/vector,
    "range"/Float32l
)

notification = "notification"/Struct(
    "caller"/Int32ul,
    "recipient"/Int32ul,
    "notification_type"/Int32ul,
    "params"/Array(3, Int32ul)
)

order_history = "order_history"/Struct(
    "order"/Int32ul,
    "action"/Int32ul,
    "time"/Int32ul,
    "position"/vector,
    "target_id"/Int32ul,
    "target_attack_category"/Int32ul,
    "target_position"/vector
)

retarget = "retarget"/Struct(
    "target_id"/Int32ul,
    "retarget_timeout"/Int32ul
)

unit_ai = "ai"/Struct(
    "mood"/Int32sl,
    "current_order"/Int32sl,
    "current_order_priority"/Int32sl,
    "current_action"/Int32sl,
    "current_target"/Int32sl,
    "current_target_type"/Int16sl,
    Padding(2),
    "current_target_location"/vector,
    "desired_target_distance"/Float32l,
    "last_action"/Int32sl,
    "last_order"/Int32sl,
    "last_target"/Int32sl,
    "last_target_type"/Int32sl,
    "last_update_type"/Int32sl,
    "idle_timer"/Int32ul,
    "idle_timeout"/Int32ul,
    "adjusted_idle_timeout"/Int32ul,
    "secondary_timer"/Int32ul,
    "look_around_timer"/Int32ul,
    "look_around_timeout"/Int32ul,
    "defend_target"/Int32sl,
    "defense_buffer"/Float32l,
    "last_world_position"/waypoint,
    "de_2006_unk"/If(lambda ctx: 26.21 > find_save_version(ctx) >= 20.06, Struct(
        "unk_float"/Float32l,
        "unk"/Int32ul
    )),
    "num_orders"/Int32ul,
    "orders"/Array(lambda ctx: ctx.num_orders, order),
    "num_notifications"/Int32ul,
    "notifications"/Array(lambda ctx: ctx.num_notifications, notification),
    "num_attacking_units"/Int32ul,
    "attacking_units"/Array(lambda ctx: ctx.num_attacking_units, Int32ul),
    "stop_after_target_killed"/Byte,
    "state"/Byte,
    "state_position_x"/Float32l,
    "state_position_y"/Float32l,
    "time_since_enemy_sighting"/Int32ul,
    "alert_mode"/Byte,
    "alert_mode_object_id"/Int32sl,
    "has_patrol_path"/Int32ul,
    If(lambda ctx: ctx.has_patrol_path > 0, path),
    "patrol_current_waypoint"/Int32ul,
    "num_order_history"/Int32ul,
    "order_history"/Array(lambda ctx: ctx.num_order_history, order_history),
    "last_retarget_time"/Int32ul,
    "randomized_retarget_timer"/Int32ul,
    "num_retarget_entries"/Int32ul,
    "retarget_entries"/Array(lambda ctx: ctx.num_retarget_entries, retarget),
    "best_unit_to_attack"/Int32sl,
    "formation_type"/Byte,
    "de_unk"/If(lambda ctx: find_version(ctx) == Version.DE, Bytes(4)),
    "de_unk_byte"/If(lambda ctx: find_save_version(ctx) >= 25.22, Byte),
    "de_unknown_2"/If(lambda ctx: find_save_version(ctx) >= 63.0 and ctx._.has_ai in (15, 17), Bytes(4))
)


combat = "combat"/Struct(
    Embedded(base_combat),
    "de_pre"/If(lambda ctx: find_version(ctx) == Version.DE and find_save_version(ctx) < 37, Bytes(4)),
    "de"/If(lambda ctx: find_version(ctx) == Version.DE, Bytes(14)),
    "de_unknown_66_3_1"/If(lambda ctx: find_save_version(ctx) >= 66.3, Bytes(4)),
    "de_2"/If(lambda ctx: find_save_version(ctx) >= 26.16, Bytes(16)),
    "de_3"/If(lambda ctx: 63 > find_save_version(ctx) >= 26.18, Bytes(1)),
    "de_4"/If(lambda ctx: find_save_version(ctx) >= 61.5, Bytes(4)),
    "de_5"/If(lambda ctx: find_save_version(ctx) >= 64.3, Bytes(19)),
    "next_volley"/Byte,
    "using_special_animation"/Byte,
    "own_base"/Byte,
    "base"/If(lambda ctx: ctx.own_base > 0, unit_type),
    "attribute_amounts"/Array(6, Int16ul),
    "decay_timer"/Int16ul,
    "raider_build_countdown"/Int32ul,
    "locked_down_count"/Int32ul,
    "inside_garrison_count"/If(lambda ctx: find_version(ctx) != Version.AOK, Byte),
    "has_ai"/Int32ul,
    "ai"/If(lambda ctx: ctx.has_ai > 0, unit_ai),
    "peek"/Peek(Bytes(5)), # TODO: figure out the right way to do this part
    "hd_position"/If(lambda ctx: find_version(ctx) == Version.HD and ctx.peek != b'\x00\xff\xff\xff\xff', Bytes(4)),
    "de_position"/If(lambda ctx: find_version(ctx) == Version.DE and ctx.peek != b'\x00\xff\xff\xff\xff', Struct(
        "position"/vector,
        "flag"/Byte,
    )),
    "town_bell_flag"/Byte,
    "town_bell_target_id"/Int32sl,
    "town_bell_target_x"/Float32l,
    "town_bell_target_y"/Float32l,
    "town_bell_target_id_2"/If(lambda ctx: find_version(ctx) != Version.AOK, Int32sl),
    "town_bell_target_type"/If(lambda ctx: find_version(ctx) != Version.AOK, Int32sl),
    "town_bell_action"/If(lambda ctx: find_version(ctx) != Version.AOK, Int32sl),
    "berserker_timer"/Float32l,
    "num_builders"/Byte,
    "num_healers"/If(lambda ctx: find_version(ctx) != Version.AOK, Byte),
    "de_unknown"/If(lambda ctx: find_save_version(ctx) >= 20.06, Int32ul),
    "de_unknown2"/If(lambda ctx: find_save_version(ctx) >= 25.01, Int32ul),
    "de_unknown3"/If(lambda ctx: 26.18 > find_save_version(ctx) >= 26.16, Bytes(5)),
    "de_unknown4"/If(lambda ctx: find_save_version(ctx) >= 26.18, Bytes(4)),
    "de_unknown5"/If(lambda ctx: find_save_version(ctx) >= 50, Bytes(48)),
    "de_unknown6"/If(lambda ctx: find_save_version(ctx) >= 61.5, Bytes(40)),
    "de_unknown7"/If(lambda ctx: find_save_version(ctx) >= 61.5, Int16ul),
    Embedded(
        IfThenElse(lambda ctx: find_save_version(ctx) >= 63.0 and ctx.has_ai == 15,
            Struct(
                "de_unknown8"/Float32l,
                "de_unknown9"/Bytes(4)
            ),
            Struct(
                "de_unknown8"/If(lambda ctx: find_save_version(ctx) >= 61.5, Bytes(2))
            )
        )
    ),
    "de_unknown_64_3_1"/If(lambda ctx: find_save_version(ctx) >= 64.3, Byte),
)

production_queue = "production_queue"/Struct(
    "unit_type_id"/Int16ul,
    "count"/Int16ul
)

building = "building"/Struct(
    Embedded(combat),
    "built"/Byte,
    "build_points"/Float32l,
    "unique_build_id"/Int32ul,
    "culture"/Byte,
    "burning"/Byte,
    "last_burn_time"/Int32ul,
    "last_garrison_time"/Int32ul,
    "relic_count"/Int32ul,
    "specific_relic_count"/Int32ul,
    "gather_point"/gatherpoint,
    "desolid_flag"/Byte,
    "pending_order"/Int32ul,
    "linked_owner"/Int32sl,
    "linked_children"/Array(lambda ctx: 3 if find_version(ctx) in (Version.DE, Version.HD) else 4, Int32sl),
    "captured_unit_count"/Byte,
    "extra_actions"/action_list,
    "research_actions"/If(lambda ctx: find_version(ctx) != Version.DE, action_list),
    "capacity"/Int16ul,
    "production_queue"/Array(lambda ctx: ctx.capacity, production_queue),
    "size"/Int16ul,
    "production_queue_total_units"/Int16ul,
    "production_queue_enabled"/Byte,
    "production_queue_actions"/action_list,
    "endpoint"/vector,
    "endpoint_2"/vector,
    "gate_locked"/Int32ul,
    "first_update"/Int32ul,
    "close_timer"/Int32ul,
    "terrain_type"/Byte,
    "semi_asleep"/Byte,
    "snow_flag"/If(lambda ctx: find_version(ctx) != Version.AOK, Byte),
    "de_flag_unk"/If(lambda ctx: find_version(ctx) == Version.DE, Byte),
    "de_unk_2"/If(lambda ctx: find_save_version(ctx) >= 20.16, Int16ul),
    "de_unk_3"/If(lambda ctx: find_save_version(ctx) >= 25.22, Byte),
    "de_unk_4"/If(lambda ctx: find_save_version(ctx) >= 26.16, Bytes(4)),
    "de_unk_5"/If(lambda ctx: find_save_version(ctx) >= 50.4, Bytes(4)),
    "de_unk_6"/If(lambda ctx: find_save_version(ctx) >= 61.5, Bytes(12)),
    "de_unk_7"/If(lambda ctx: find_save_version(ctx) >= 64.3, Bytes(4)),
    "de_unknown_66_3_2"/If(lambda ctx: find_save_version(ctx) >= 66.3, Bytes(5)),
)


# Objects that exist on the map at the start of the recorded game
existing_object = "objects"/Struct(
    "type"/Byte,
    "player_id"/Byte,
    Embedded("properties"/Switch(lambda ctx: ctx.type, {
        10: static,
        20: animated,
        25: animated,
        30: moving,
        40: action,
        50: base_combat,
        60: missile,
        70: combat,
        80: building,
        90: static
    }, default=Pass))
)

# Default values for objects, nothing of real interest
default_object = "default_object"/Struct(
    ObjectTypeEnum("type"/Byte),
    Padding(14),
    "properties"/Switch(lambda ctx: ctx.type, {
        "gaia": Padding(24),
        "object": Padding(32),
        "fish": Padding(32),
        "other": Padding(28),
    }, default="end_of_object"/Find(b'\x21\x16', 200))
)
