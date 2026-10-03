module src

import velo.assets
import velo.core
import velo.kine2d
import velo.render

// Dragon — a dragon on the bench or in a battle slot. Its level picks the Kine2D files (characters/dragon<level>.*) and the
// fireball stats. In a battle slot it plays `attack` and shoots the monster closest to the wall; on the bench it only idles.
// Game moves it (drag and drop, merging) by changing `home`; the dragon glides there by itself.
pub struct Dragon {
	core.Component
pub mut:
	level   int = 1
	cell    int = -1 @[hide] // index into Game.cells
	battle  bool     @[hide] // in a battle slot (shoots)
	dragged bool     @[hide]
	home    core.Vec2 @[hide]
	cooldown f32     @[hide]
	fire_in  f32 = -1 @[hide] // time until the fireball leaves the mouth once the attack animation started
	attacking bool   @[hide]
	pop      f32     @[hide] // squash-and-stretch after a merge or summon
	game    &Game = unsafe { nil } @[hide]
	skel    &kine2d.Kine2D = unsafe { nil } @[hide]
}

// setup gets a pooled node ready as a new dragon.
pub fn (mut d Dragon) setup(g &Game, level int, cell int, at core.Vec2) {
	d.game = unsafe { g }
	d.cell = cell
	d.dragged = false
	d.attacking = false
	d.fire_in = -1
	d.cooldown = 0.3
	d.node.position = at
	d.node.scale = core.vec2(1, 1)
	d.node.z_index = 0
	d.home = at
	if d.skel == unsafe { nil } {
		d.skel = d.node.find('Body') or { return }.get_component[kine2d.Kine2D]() or { return }
	}
	d.set_level(level)
	d.pop = 1
}

// set_level switches to the rig and stats of `level`.
pub fn (mut d Dragon) set_level(level int) {
	d.level = clamp_level(level)
	if d.skel != unsafe { nil } {
		d.skel.data = assets.ref[assets.TextAsset]('characters/dragon${d.level}.skel.json')
		d.skel.atlas = assets.ref[assets.TextAsset]('characters/dragon${d.level}.atlas.json')
		d.skel.play('idle', true)
	}
	d.attacking = false
	d.fire_in = -1
	if mut b := d.node.find('Badge/Text') {
		if mut l := b.get_component[render.Label]() {
			l.text = '${d.level}'
		}
	}
}

pub fn (mut d Dragon) update(dt f32) {
	if !d.dragged {
		p := d.node.position
		k := clamp_f(dt * 16, 0, 1)
		d.node.position = p + (d.home - p).mul(k)
	}
	if d.pop > 0 {
		d.pop -= dt * 2.6
		if d.pop < 0 {
			d.pop = 0
		}
		s := 1 + f32(0.3) * d.pop * d.pop
		d.node.scale = core.vec2(s, s)
	} else if d.dragged {
		d.node.scale = core.vec2(1.12, 1.12)
	} else {
		d.node.scale = core.vec2(1, 1)
	}
	if d.game == unsafe { nil } || !d.battle || d.dragged || !d.game.running() {
		return
	}
	if d.attacking && d.skel != unsafe { nil } && d.skel.finished {
		d.skel.play('idle', true)
		d.attacking = false
	}
	if d.fire_in >= 0 {
		d.fire_in -= dt
		if d.fire_in < 0 {
			d.shoot()
		}
		return
	}
	d.cooldown -= dt
	if d.cooldown <= 0 {
		if _ := d.game.front_enemy() {
			d.cooldown = dragon_stats(d.level).cooldown
			d.fire_in = 0.2
			d.attacking = true
			if d.skel != unsafe { nil } {
				d.skel.play('attack', false)
			}
		}
	}
}

fn (mut d Dragon) shoot() {
	mut g := d.game
	target := g.front_enemy() or { return }
	st := dragon_stats(d.level)
	g.fire(d.node.position + core.vec2(0, -42), target, st)
	play_sfx(g.scene(), 'fire', 0.85 + f32(d.level) * 0.06)
}
