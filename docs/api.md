# API Reference

This page documents the public `aj.` namespace. All functions and classes listed here are available directly from `ajishio`.

## Game Objects

::: ajishio.game_object.GameObject
    # Alias: `aj.GameObject`

## Engine Control

::: ajishio.engine.Engine.game_start_async
    # Alias: `aj.game_start_async`
::: ajishio.engine.Engine.audio_is_playing
    # Alias: `aj.audio_is_playing`
::: ajishio.engine.Engine.audio_play_sound
    # Alias: `aj.audio_play_sound`
::: ajishio.engine.Engine.collision_rectangle
    # Alias: `aj.collision_rectangle`
::: ajishio.engine.Engine.collision_rectangle_list
    # Alias: `aj.collision_rectangle_list`
::: ajishio.engine.Engine.game_end
    # Alias: `aj.game_end`
::: ajishio.engine.Engine.game_restart
    # Alias: `aj.game_restart`
::: ajishio.engine.Engine.game_set_speed
    # Alias: `aj.game_set_speed`
::: ajishio.engine.Engine.game_start
    # Alias: `aj.game_start`
::: ajishio.engine.Engine.instance_count
    # Alias: `aj.instance_count`
::: ajishio.engine.Engine.instance_destroy
    # Alias: `aj.instance_destroy`
::: ajishio.engine.Engine.instance_exists
    # Alias: `aj.instance_exists`
::: ajishio.engine.Engine.instance_find
    # Alias: `aj.instance_find`
::: ajishio.engine.Engine.instance_position
    # Alias: `aj.instance_position`
::: ajishio.engine.Engine.instances_iterate
    # Alias: `aj.instances_iterate`
::: ajishio.engine.Engine.register_objects
    # Alias: `aj.register_objects`
::: ajishio.engine.Engine.room_goto
    # Alias: `aj.room_goto`
::: ajishio.engine.Engine.room_goto_next
    # Alias: `aj.room_goto_next`
::: ajishio.engine.Engine.room_goto_previous
    # Alias: `aj.room_goto_previous`
::: ajishio.engine.Engine.room_restart
    # Alias: `aj.room_restart`
::: ajishio.engine.Engine.room_set_background
    # Alias: `aj.room_set_background`
::: ajishio.engine.Engine.room_set_height
    # Alias: `aj.room_set_height`
::: ajishio.engine.Engine.room_set_size
    # Alias: `aj.room_set_size`
::: ajishio.engine.Engine.room_set_width
    # Alias: `aj.room_set_width`
::: ajishio.engine.Engine.set_rooms
    # Alias: `aj.set_rooms`
::: ajishio.engine.Engine.view_set_hport
    # Alias: `aj.view_set_hport`
::: ajishio.engine.Engine.view_set_wport
    # Alias: `aj.view_set_wport`
::: ajishio.engine.Engine.view_set_xport
    # Alias: `aj.view_set_xport`
::: ajishio.engine.Engine.view_set_yport
    # Alias: `aj.view_set_yport`
::: ajishio.engine.Engine.window_set_size
    # Alias: `aj.window_set_size`

## Rendering

::: ajishio.rendering.Renderer.draw_circle
    # Alias: `aj.draw_circle`
::: ajishio.rendering.Renderer.draw_line
    # Alias: `aj.draw_line`
::: ajishio.rendering.Renderer.draw_rectangle
    # Alias: `aj.draw_rectangle`
::: ajishio.rendering.Renderer.draw_set_font
    # Alias: `aj.draw_set_font`
::: ajishio.rendering.Renderer.draw_sprite
    # Alias: `aj.draw_sprite`
::: ajishio.rendering.Renderer.draw_text
    # Alias: `aj.draw_text`
::: ajishio.rendering.Renderer.draw_triangle
    # Alias: `aj.draw_triangle`
::: ajishio.rendering.load_font
    # Alias: `aj.load_font`
::: ajishio.rendering.make_color_hsv
    # Alias: `aj.make_color_hsv`
::: ajishio.rendering.Renderer.text_height
    # Alias: `aj.text_height`
::: ajishio.rendering.Renderer.text_width
    # Alias: `aj.text_width`

## Input

::: ajishio.input.keyboard_check
    # Alias: `aj.keyboard_check`
::: ajishio.input.keyboard_check_pressed
    # Alias: `aj.keyboard_check_pressed`
::: ajishio.input.keyboard_check_released
    # Alias: `aj.keyboard_check_released`
::: ajishio.input.mouse_check_button
    # Alias: `aj.mouse_check_button`
::: ajishio.input.mouse_check_button_pressed
    # Alias: `aj.mouse_check_button_pressed`
::: ajishio.input.mouse_check_button_released
    # Alias: `aj.mouse_check_button_released`
::: ajishio.input.mouse_wheel_down
    # Alias: `aj.mouse_wheel_down`
::: ajishio.input.mouse_wheel_up
    # Alias: `aj.mouse_wheel_up`
::: ajishio.input.ord
    # Alias: `aj.ord`

## Utilities

::: ajishio.utils.clamp
    # Alias: `aj.clamp`
::: ajishio.utils.lengthdir_x
    # Alias: `aj.lengthdir_x`
::: ajishio.utils.lengthdir_y
    # Alias: `aj.lengthdir_y`
::: ajishio.utils.lerp
    # Alias: `aj.lerp`
::: ajishio.utils.map_value
    # Alias: `aj.map_value`
::: ajishio.utils.point_distance
    # Alias: `aj.point_distance`
::: ajishio.utils.profile
    # Alias: `aj.profile`
::: ajishio.utils.room_set_caption
    # Alias: `aj.room_set_caption`
::: ajishio.utils.sign
    # Alias: `aj.sign`

## Types & Constants

::: ajishio.types.CollisionMask
    # Alias: `aj.CollisionMask`
::: ajishio.CustomFields
::: ajishio.types.Entity
    # Alias: `aj.Entity`
::: ajishio.types.GameLevel
    # Alias: `aj.GameLevel`
::: ajishio.types.GameObjectKwargs
    # Alias: `aj.GameObjectKwargs`
::: ajishio.types.GameSprite
    # Alias: `aj.GameSprite`
::: ajishio.types.IGameObject
    # Alias: `aj.IGameObject`

## Asset Loaders

::: ajishio.sprite_loader.load_aseprite_sprite
    # Alias: `aj.load_aseprite_sprite`
::: ajishio.sprite_loader.load_aseprite_sprites
    # Alias: `aj.load_aseprite_sprites`
::: ajishio.sprite_loader.sprite_set_offset
    # Alias: `aj.sprite_set_offset`

## Asset Loaders

::: ajishio.sound_loader.load_sound
    # Alias: `aj.load_sound`
::: ajishio.sound_loader.load_sounds
    # Alias: `aj.load_sounds`

## Asset Loaders

::: ajishio.level_loader.load_ldtk_levels
    # Alias: `aj.load_ldtk_levels`

## Audio

::: ajishio.game_sound.GameSound
    # Alias: `aj.GameSound`

## Other

::: ajishio.c_aqua
::: ajishio.c_black
::: ajishio.c_blue
::: ajishio.c_dkgray
::: ajishio.c_fuchsia
::: ajishio.c_gray
::: ajishio.c_green
::: ajishio.c_lime
::: ajishio.c_ltgray
::: ajishio.c_maroon
::: ajishio.c_navy
::: ajishio.c_olive
::: ajishio.c_orange
::: ajishio.c_purple
::: ajishio.c_red
::: ajishio.c_silver
::: ajishio.c_teal
::: ajishio.c_white
::: ajishio.c_yellow
::: ajishio.delta_time
::: ajishio.mb_left
::: ajishio.mb_middle
::: ajishio.mb_right
::: ajishio.room
::: ajishio.room_background_color
::: ajishio.room_height
::: ajishio.room_speed
::: ajishio.room_width
::: ajishio.view_current
::: ajishio.view_hport
::: ajishio.view_wport
::: ajishio.view_xport
::: ajishio.view_yport
::: ajishio.vk_backspace
::: ajishio.vk_down
::: ajishio.vk_enter
::: ajishio.vk_escape
::: ajishio.vk_left
::: ajishio.vk_right
::: ajishio.vk_space
::: ajishio.vk_up
::: ajishio.window_height
::: ajishio.window_width