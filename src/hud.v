module src

import velo.core
import velo.render

// Hud — the on-screen UI of scenes/main.scene (prefabs/hud.scene): numbers, the summon button, hints, the wave banner,
// pause / speed and the end-of-game dialog. It sits on a node with `unscaled_time` so it keeps working while paused.
pub struct Hud {
	core.Component
}

fn (h &Hud) clicked(path string) bool {
	n := h.node.find(path) or { return false }
	b := n.get_component[render.Button]() or { return false }
	return b.clicked
}

fn (mut h Hud) set_text(path string, text string) {
	if mut n := h.node.find(path) {
		if mut l := n.get_component[render.Label]() {
			l.text = text
		}
	}
}

fn (mut h Hud) set_color(path string, color core.Color) {
	if mut n := h.node.find(path) {
		if mut l := n.get_component[render.Label]() {
			l.color = color
		}
	}
}

fn (mut h Hud) set_active(path string, on bool) {
	if mut n := h.node.find(path) {
		n.active = on
	}
}

pub fn (mut h Hud) update(dt f32) {
	mut g := game_of(h.scene()) or { return }
	mut sc := h.scene()
	h.set_text('Top/Lives/Text', '${g.lives}')
	h.set_text('Top/Gold/Text', '${g.gold}')
	h.set_text('Top/Wave/Text', '${if g.wave == 0 { 1 } else { g.wave }}')
	h.set_text('Top/Speed/Text', if sc.time_scale > 1 { 'x2' } else { 'x1' })

	if h.clicked('Top/Speed') {
		g.toggle_speed()
	}
	if h.clicked('Top/Pause') {
		g.toggle_pause()
		play_sfx(sc, 'click', 1)
	}
	if h.clicked('Summon') {
		g.summon()
	}
	if h.clicked('Overlay/Box/Resume') {
		g.toggle_pause()
	}
	if h.clicked('Overlay/Box/Restart') {
		g.restart()
		return
	}
	if h.clicked('Overlay/Box/Menu') {
		g.to_menu()
		return
	}

	// summon button: price turns red when it is too high
	cost := g.summon_cost()
	h.set_text('Summon/Cost', '${cost}')
	h.set_color('Summon/Cost', if g.gold >= cost { core.rgba(255, 224, 90, 255) } else { core.rgba(255, 120, 110, 255) })

	// hint line
	if mut n := h.node.find('Hint') {
		n.active = g.hint_time > 0 && g.phase == .playing
		if mut l := n.get_component[render.Label]() {
			l.text = g.hint
			l.color = core.rgba(255, 255, 255, u8(255 * clamp_f(g.hint_time / 0.4, 0, 1)))
		}
	}

	// wave banner: fades out
	if mut n := h.node.find('Banner') {
		n.active = g.banner_time > 0 && g.phase == .playing
		if mut l := n.get_component[render.Label]() {
			l.text = g.banner
			l.color = core.rgba(255, 236, 150, u8(255 * clamp_f(g.banner_time / 0.5, 0, 1)))
		}
	}

	// dialog: pause or defeat
	over := g.phase == .lost
	h.set_active('Overlay', sc.paused || over)
	if sc.paused || over {
		h.set_active('Overlay/Box/Resume', sc.paused && !over)
		title, sub := if over {
			'Defeat', 'The city fell on wave ${g.wave}.\n${g.kills} monsters slain, best dragon: ${dragon_stats(g.top_level).name}'
		} else {
			'Paused', 'Wave ${if g.wave == 0 { 1 } else { g.wave }}'
		}
		h.set_text('Overlay/Box/Title', title)
		h.set_text('Overlay/Box/Sub', sub)
	}
}
