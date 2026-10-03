module main

import os
import src
import velo.app
import velo.editor

//   velo run      run the game
//   velo editor   open the scene/prefab editor
//   velo run ios-sim | android      play on a phone (portrait touch)
// The game logic lives in src/, the art, sounds, prefabs and scenes in assets/ (made by tools/gen_assets.py).
fn main() {
	// On Android/iOS the packaged assets are used instead (see app.new).
	assets_dir := os.join_path(os.dir(@FILE), 'assets')
	if '--editor' in os.args {
		mut ed := editor.new(
			title:      'Dragon City — Velo Editor'
			assets_dir: assets_dir
			scene:      'scenes/main.scene'
		) or {
			eprintln(err)
			exit(1)
		}
		src.register_components(mut ed.registry)
		ed.run()
		return
	}
	mut game := app.new(
		title:         'Dragon City'
		app_id:        'dragon-city'
		assets_dir:    assets_dir
		scene:         'scenes/menu.scene'
		width:         540 // design resolution: a portrait phone, fitted to any window or screen (see scale_mode)
		height:        960
		window_width:  450 // desktop window: same aspect ratio, small enough for a laptop screen
		window_height: 800
		scale_mode:    'expand'
	) or {
		eprintln(err)
		exit(1)
	}
	src.register_components(mut game.registry)
	game.run()
}
