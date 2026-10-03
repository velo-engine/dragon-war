module src

import velo.audio
import velo.core
import velo.render

// play_sfx plays the AudioSource named `name` under the scene's Audio node (prefabs/audio.scene).
pub fn play_sfx(sc &core.Scene, name string, pitch f32) {
	n := sc.find('Audio/${name}') or { return }
	if mut a := n.get_component[audio.AudioSource]() {
		a.pitch = pitch
		a.play_one_shot()
	}
}

pub fn game_of(sc &core.Scene) ?&Game {
	n := sc.find('Game')?
	return n.get_component[Game]()
}

// FloatText — a short text (gold, merge level) that rises and fades, then the pool takes its node back.
pub struct FloatText {
	core.Component
pub mut:
	rise  f32 = 34
	life  f32 = 0.9
	age   f32  @[hide]
	start core.Color = core.white @[hide]
}

pub fn (mut f FloatText) launch(text string, at core.Vec2, color core.Color) {
	f.age = 0
	f.start = color
	f.node.position = at
	if mut l := f.node.get_component[render.Label]() {
		l.text = text
		l.color = color
	}
}

pub fn (mut f FloatText) update(dt f32) {
	f.age += dt
	t := clamp_f(f.age / f.life, 0, 1)
	f.node.position.y -= f.rise / f.life * dt
	if mut l := f.node.get_component[render.Label]() {
		a := if t < 0.55 { f32(1) } else { 1 - (t - 0.55) / 0.45 }
		l.color = core.rgba(f.start.r, f.start.g, f.start.b, u8(255 * a))
	}
}
