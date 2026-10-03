module src

import os
import velo.core
import velo.render

// MenuScreen — the title screen: Play starts the game and the best result (save data) is shown.
pub struct MenuScreen {
	core.Component
pub mut:
	game string = 'scenes/main.scene'
}

pub fn (mut m MenuScreen) start() {
	st := m.scene().store
	best := st.get_int('best_wave', 0)
	top := st.get_int('best_dragon', 0)
	if mut n := m.node.find('Best') {
		if mut l := n.get_component[render.Label]() {
			l.text = if best == 0 {
				'Drag dragons up, merge two alike'
			} else {
				'Best: wave ${best}   Top dragon: ${dragon_stats(top).name}'
			}
		}
	}
	if mut title := m.node.find('Title') {
		title.scale = core.vec2(0.7, 0.7)
		title.tween().scale_to(core.vec2(1, 1), 0.7, .elastic_out)
	}
}

pub fn (mut m MenuScreen) update(dt f32) {
	play := m.node.find('Play') or { return }
	b := play.get_component[render.Button]() or { return }
	if b.clicked || os.getenv('DC_AUTO') != '' || m.input().was_pressed(.enter) || m.input().was_pressed(.space) {
		play_sfx(m.scene(), 'click', 1)
		mut sc := m.scene()
		sc.change_scene(m.game, fade: 0.4)
	}
}
