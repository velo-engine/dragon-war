module src

import math
import rand
import velo.core
import velo.kine2d
import velo.render

// Enemy — a monster marching down the battlefield toward the wall. Its node comes from a Pool (Game.spawn_enemy):
// `spawn` resets it for a new life, `recycle` gives the node back. Prefab children: Body (Kine2D), Bar, Shadow.
pub struct Enemy {
	core.Component
pub mut:
	kind   string = 'goblin'
	hp     f32          @[hide]
	max_hp f32          @[hide]
	speed  f32          @[hide]
	reward int          @[hide]
	leak   int          @[hide]
	uid    int          @[hide] // changes on every spawn, so a fireball can tell its target was recycled
	alive  bool         @[hide]
	dying  f32          @[hide] // seconds left of the death animation
	flash  f32          @[hide]
	age    f32          @[hide]
	lane_x f32          @[hide]
	phase  f32          @[hide]
	sway   f32          @[hide]
	game   &Game = unsafe { nil } @[hide]
	skel   &kine2d.Kine2D = unsafe { nil } @[hide]
	bar    &render.ProgressBar = unsafe { nil } @[hide]
}

// spawn starts a new life at the top of the field.
pub fn (mut e Enemy) spawn(g &Game, uid int, wave int) {
	st := enemy_stats(e.kind)
	e.game = unsafe { g }
	e.uid = uid
	e.max_hp = st.hp * wave_hp_scale(wave)
	e.hp = e.max_hp
	e.speed = st.speed * (1 + f32(wave) * 0.01)
	e.reward = st.reward
	e.leak = st.leak
	e.alive = true
	e.dying = 0
	e.flash = 0
	e.age = 0
	e.phase = rand.f32() * 6.28
	e.sway = 4 + rand.f32() * 8
	e.lane_x = lane_min + rand.f32() * (lane_max - lane_min)
	e.node.position = core.vec2(e.lane_x, spawn_y - rand.f32() * 14)
	if e.skel == unsafe { nil } {
		e.skel = e.node.find('Body') or { return }.get_component[kine2d.Kine2D]() or { return }
	}
	if e.bar == unsafe { nil } {
		e.bar = e.node.find('Bar') or { return }.get_component[render.ProgressBar]() or { return }
	}
	e.skel.color = core.white
	e.skel.speed = clamp_f(e.speed / 46, 0.7, 2)
	e.skel.play('walk', true)
	e.bar.progress = 1
	if mut b := e.node.find('Bar') {
		b.active = true
	}
}

pub fn (e &Enemy) pos() core.Vec2 {
	return e.node.position
}

pub fn (mut e Enemy) update(dt f32) {
	if e.dying > 0 {
		e.dying -= dt
		if e.dying <= 0 {
			release_node(e.node)
		}
		return
	}
	if !e.alive {
		return
	}
	e.age += dt
	if e.flash > 0 {
		e.flash -= dt
		if e.skel != unsafe { nil } {
			e.skel.color = if e.flash > 0 { core.rgba(255, 130, 130, 255) } else { core.white }
		}
	}
	e.node.position.y += e.speed * dt
	e.node.position.x = clamp_f(e.lane_x + f32(math.sin(f64(e.age) * 1.6 + f64(e.phase))) * e.sway, lane_min - 20, lane_max + 20)
	if e.node.position.y >= wall_y {
		e.reach_wall()
	}
}

fn (mut e Enemy) reach_wall() {
	e.alive = false
	mut g := e.game
	g.on_leak(e, e.leak)
	release_node(e.node)
}

// hurt deals damage; the last hit starts the death animation.
pub fn (mut e Enemy) hurt(amount f32) {
	if !e.alive {
		return
	}
	e.hp -= amount
	e.flash = 0.08
	if e.skel != unsafe { nil } {
		e.skel.color = core.rgba(255, 130, 130, 255)
	}
	if e.bar != unsafe { nil } {
		e.bar.progress = if e.hp > 0 { e.hp / e.max_hp } else { 0 }
	}
	if e.hp <= 0 {
		e.die()
	}
}

fn (mut e Enemy) die() {
	e.alive = false
	e.dying = 0.65
	if e.skel != unsafe { nil } {
		e.skel.color = core.white
		e.skel.speed = 1
		e.skel.play('die', false)
	}
	if mut b := e.node.find('Bar') {
		b.active = false
	}
	mut g := e.game
	g.on_kill(e)
}
