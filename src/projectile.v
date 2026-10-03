module src

import math
import velo.core
import velo.render

// Projectile — a dragon fireball. It flies to its target, switches to another monster if the target died on the way,
// and explodes on arrival. The node comes from Game's bullet Pool and goes back to it after the hit.
pub struct Projectile {
	core.Component
pub mut:
	speed  f32
	damage f32
	splash f32
	age    f32           @[hide]
	uid    int           @[hide]
	target &Enemy = unsafe { nil } @[hide]
	dest   core.Vec2     @[hide]
	game   &Game = unsafe { nil } @[hide]
}

// launch fires from `from` at `target` with the stats of a dragon level.
pub fn (mut p Projectile) launch(g &Game, from core.Vec2, target &Enemy, st DragonStats) {
	p.game = unsafe { g }
	p.age = 0
	p.speed = st.speed
	p.damage = st.damage
	p.splash = st.splash
	p.node.position = from
	p.node.scale = core.vec2(st.scale, st.scale)
	p.aim(target)
	if mut s := p.node.get_component[render.Sprite]() {
		s.color = st.color
	}
	if mut t := p.node.find('Trail') {
		if mut ps := t.get_component[render.ParticleSystem]() {
			ps.start_color = st.color
			ps.end_color = core.rgba(st.color.r, st.color.g / 2, 20, 0)
			ps.clear()
		}
	}
}

fn (mut p Projectile) aim(target &Enemy) {
	p.target = unsafe { target }
	p.uid = target.uid
	p.dest = target.pos()
}

fn (p &Projectile) target_alive() bool {
	return p.target != unsafe { nil } && p.target.alive && p.target.uid == p.uid
}

pub fn (mut p Projectile) update(dt f32) {
	p.age += dt
	if !p.target_alive() {
		if e := p.game.front_enemy() {
			p.aim(e)
		}
	}
	if p.target_alive() {
		p.dest = p.target.pos()
	}
	here := p.node.position
	to := p.dest - here
	d := to.length()
	step := p.speed * dt
	if d <= step + 6 || p.age > 3 {
		p.impact()
		return
	}
	dir := to.mul(1 / d)
	p.node.position = here + dir.mul(step)
	p.node.rotation = f32(math.atan2(f64(dir.y), f64(dir.x)) * 180.0 / math.pi)
}

fn (mut p Projectile) impact() {
	mut g := p.game
	if p.splash > 0 {
		g.spawn_fx('boom', p.dest)
		play_sfx(g.scene(), 'explode', 1.1 - p.splash / 400)
		// backwards: a killed monster leaves the list while we walk it
		for i := g.enemies.len - 1; i >= 0; i-- {
			if i >= g.enemies.len {
				continue
			}
			mut e := g.enemies[i]
			if e.alive && e.pos().distance(p.dest) <= p.splash {
				e.hurt(p.damage)
			}
		}
	} else if p.target_alive() {
		g.spawn_fx('hit', p.dest)
		play_sfx(g.scene(), 'hit', 1)
		mut e := p.target
		e.hurt(p.damage)
	}
	release_node(p.node)
}
