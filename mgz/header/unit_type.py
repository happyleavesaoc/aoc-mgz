"""Unit Types."""
from construct import (
    Struct, Float32l, Int16ul, Byte, Embedded, Switch, If,
    Int32ul, Array, String, Padding, IfThenElse, this
)
from mgz.util import find_version, Version

attribute = "attribute"/Struct(
    "type"/Int16ul,
    "amount"/Float32l,
    "flag"/Byte
)

damage_sprite = "damage_sprite"/Struct(
    "sprite"/Int16ul,
    "damage_percent"/Int16ul,
    "flag"/Byte
)

base = "base"/Struct(
    "name_len"/Int16ul,
    "id"/Int16ul,
    "string_id"/Int16ul,
    "string_id_2"/Int16ul,
    "unit_class"/Int16ul,
    "standing_sprite_1"/Int16ul,
    "standing_sprite_2"/Int16ul,
    "dying_sprite"/Int16ul,
    "undead_sprite"/Int16ul,
    "undead_flag"/Byte,
    "hitpoints"/Int16ul,
    "los"/Float32l,
    "garrison_capacity"/Byte,
    "radius"/Struct(
        "x"/Float32l,
        "y"/Float32l,
        "z"/Float32l
    ),
    "train_sound"/Int16ul,
    "damage_sound"/Int16ul,
    "death_spawn"/Int16ul,
    "sort_number"/Byte,
    "can_be_built_on"/Byte,
    "button_picture"/Int16ul,
    "hide_in_editor"/Byte,
    "portrait"/Int16ul,
    "enabled"/Byte,
    "disabled"/Byte,
    "tile_req"/Struct(
        "x"/Int16ul,
        "y"/Int16ul
    ),
    "center_tile_req"/Struct(
        "x"/Int16ul,
        "y"/Int16ul
    ),
    "construction_radius"/Struct(
        "x"/Float32l,
        "y"/Float32l
    ),
    "elevation_flag"/Byte,
    "fog_flag"/Byte,
    "terrain_restriction_id"/Int16ul,
    "movement_type"/Byte,
    "attribute_max"/Int16ul,
    "attribute_rot"/Float32l,
    "area_effect_level"/Byte,
    "combat_level"/Byte,
    "select_level"/Byte,
    "map_draw_level"/Byte,
    "unit_level"/Byte,
    "multiple_attribute_mod"/Float32l,
    "map_color"/Byte,
    "help_string_id"/Int32ul,
    "help_page_id"/Int32ul,
    "hotkey_id"/Int32ul,
    "recyclable"/Byte,
    "track_as_resource"/Byte,
    "create_doppleganger"/Byte,
    "resource_group"/Byte,
    "occlusion_mask"/Byte,
    "obstruction_type"/Byte,
    "selection_shape"/Byte,
    "object_flags"/If(lambda ctx: find_version(ctx) != Version.AOK, Int32ul),
    "civilization"/Byte,
    "attribute_piece"/Byte,
    "outline_radius"/Struct(
        "x"/Float32l,
        "y"/Float32l,
        "z"/Float32l
    ),
    "attributes"/Array(3, attribute),
    "num_damage_sprites"/Byte,
    "damage_sprites"/Array(this.num_damage_sprites, damage_sprite),
    "selected_sound"/Int16ul,
    "death_sound"/Int16ul,
    "attack_reaction"/Byte,
    "convert_terrain_flag"/Byte,
    "name"/String(this.name_len),
    "copy_id"/Int16ul,
    "group"/Int16ul
)

animated = "animated"/Struct(
    base,
    "speed"/Float32l
)

moving = "moving"/Struct(
    animated,
    "move_sprite"/Int16ul,
    "run_sprite"/Int16ul,
    "turn_speed"/Float32l,
    "size_class"/Byte,
    "trailing_unit"/Int16ul,
    "trailing_options"/Byte,
    "trailing_spacing"/Float32l,
    "move_algorithm"/Byte,
    "turn_radius"/Float32l,
    "turn_radius_speed"/Float32l,
    "maximum_yaw_per_second_moving"/Float32l,
    "stationary_yaw_per_revolution_time"/Float32l,
    "maximum_yaw_per_second_stationary"/Float32l
)

action = "action"/Struct(
    moving,
    "default_task"/Int16ul,
    "search_radius"/Float32l,
    "work_rate"/Float32l,
    "drop_site"/Int16ul,
    "backup_drop_site"/Int16ul,
    "task_by_group"/Byte,
    "command_sound"/Int16ul,
    "move_sound"/Int16ul,
    "run_pattern"/Byte
)

weapon = "weapon"/Struct(
    "type"/Int16ul,
    "value"/Int16ul
)

base_combat = "base_combat"/Struct(
    action,
    "base_armour"/IfThenElse(lambda ctx: find_version(ctx) != Version.AOK, Int16ul, Byte),
    "num_weapons"/Int16ul,
    "weapons"/Array(this.num_weapons, weapon),
    "num_armours"/Int16ul,
    "armours"/Array(this.num_armours, weapon),
    "defense_terrain_bonus"/Int16ul,
    "weapon_range_max"/Float32l,
    "area_effect_range"/Float32l,
    "attack_speed"/Float32l,
    "missile_id"/Int16ul,
    "base_hit_chance"/Int16ul,
    "break_off_combat"/Byte,
    "frame_delay"/Int16ul,
    "weapon_offset"/Struct(
        "x"/Float32l,
        "y"/Float32l,
        "z"/Float32l
    ),
    "blast_level_offense"/Byte,
    "weapon_range_min"/Float32l,
    "missed_missile_spread"/Float32l,
    "fight_sprite"/Int16ul,
    "displayed_armour"/Int16ul,
    "displayed_attack"/Int16ul,
    "displayed_range"/Float32l,
    "displayed_reload_time"/Float32l
)

missile = "missile"/Struct(
    base_combat,
    "missile_type"/Byte,
    "targeting_type"/Byte,
    "missile_hit_info"/Byte,
    "missile_die_info"/Byte,
    "area_effect_specials"/Byte,
    "ballistics_ratio"/Float32l
)

attribute_cost = "cost"/Struct(
    "type"/Int16ul,
    "amount"/Int16ul,
    "flag"/Byte,
    Padding(1)
)

combat = "combat"/Struct(
    base_combat,
    "cost"/Array(3, attribute_cost),
    "create_time"/Int16ul,
    "create_at_building"/Int16ul,
    "creat_button"/Byte,
    "rear_attack_modifieer"/Float32l,
    "flank_attack_modifier"/Float32l,
    "tribe_unit_type"/Byte,
    "hero_flag"/Byte,
    "garrison_sprite"/Int32ul,
    "volley_fire_aount"/Float32l,
    "max_attacks_in_volley"/Byte,
    "volley_spread"/Struct(
        "x"/Float32l,
        "y"/Float32l
    ),
    "volley_start_spread_adjustment"/Float32l,
    "volley_missile"/Int32ul,
    "special_attack_sprite"/Int32ul,
    "special_attack_flag"/Byte,
    "displayed_pierce_armour"/Int16ul
)

linked_building = "link"/Struct(
    "unit_id"/Int16ul,
    "x_offset"/Float32l,
    "y_offset"/Float32l
)

building = "building"/Struct(
    combat,
    "construction_sprite"/Int16ul,
    "snow_sprite"/If(lambda ctx: find_version(ctx) != Version.AOK, Int16ul),
    "connect_flag"/Byte,
    "facet"/Int16ul,
    "destroy_on_build"/Byte,
    "on_build_make_unit"/Int16ul,
    "on_build_make_tile"/Int16ul,
    "on_build_make_overlay"/Int16ul,
    "on_build_make_tech"/Int16ul,
    "can_burn"/Byte,
    "linked_buildings"/Array(4, linked_building),
    "construction_unit"/Int16ul,
    "transform_unit"/Int16ul,
    "transform_sound"/Int16ul,
    "construction_sound"/Int16ul,
    "garrison_type"/Byte,
    "garrison_heal_rate"/Float32l,
    "garrison_repair_rate"/Float32l,
    "salvage_unit"/Int16ul,
    "salvage_attributes"/Array(6, Byte)
)

unit_type = "unit_type"/Struct(
    "type"/Byte,
    Embedded("properties"/Switch(this.type, {
        10: base,
        15: base,
        20: animated,
        25: animated,
        30: moving,
        40: action,
        50: base_combat,
        60: missile,
        70: combat,
        80: building
    }))
)
