module src

import velo.core
import velo.render

// Pool — keeps finished nodes (monsters, fireballs, dragons, effects, floating texts) to reuse them instead of
// instantiating a prefab and destroying the node again. A pooled node is created once from its prefab, then switched
// off (`active = false`: it is neither updated nor drawn) when it is released and switched on when acquired.
// Its skeleton, textures and component state stay loaded, so reusing a monster costs next to nothing.
@[heap]
pub struct Pool {
pub:
	prefab string
pub mut:
	parent  &core.Node = unsafe { nil }
	free    []&core.Node
	created int // nodes made so far (grows only when the pool ran dry)
}

pub fn new_pool(prefab string, parent &core.Node) &Pool {
	return &Pool{
		prefab: prefab
		parent: unsafe { parent }
	}
}

// prewarm creates `count` nodes up front so no prefab is instantiated during play.
pub fn (mut p Pool) prewarm(mut sc core.Scene, count int) {
	for _ in 0 .. count {
		mut n := p.create(mut sc) or { return }
		p.release(mut n)
	}
}

// acquire hands out a switched-on node: a recycled one, or a new one when the pool is empty.
// `life` > 0 releases it again by itself after that many seconds (effects, texts).
pub fn (mut p Pool) acquire(mut sc core.Scene, life f32) ?&core.Node {
	mut n := if p.free.len > 0 { p.free.pop() } else { p.create(mut sc)? }
	n.active = true
	if mut item := n.get_component[PoolItem]() {
		item.pooled = false
		item.life = life
	}
	return n
}

// release takes a node back. Releasing twice is harmless.
pub fn (mut p Pool) release(mut n core.Node) {
	mut item := n.get_component[PoolItem]() or { return }
	if item.pooled {
		return
	}
	item.pooled = true
	item.life = 0
	n.active = false
	p.free << n
}

fn (mut p Pool) create(mut sc core.Scene) ?&core.Node {
	mut parent := p.parent
	mut n := sc.instantiate(p.prefab, mut parent) or {
		eprintln('[pool] ${p.prefab}: ${err}')
		return none
	}
	n.add_component(&PoolItem{
		pool: p
	})
	p.created++
	return n
}

// PoolItem — added to every pooled node: remembers its pool and releases the node after `life` seconds.
pub struct PoolItem {
	core.Component
pub mut:
	pool   &Pool = unsafe { nil } @[hide]
	life   f32                    @[hide]
	pooled bool                   @[hide]
}

pub fn (mut i PoolItem) update(dt f32) {
	if i.life > 0 {
		i.life -= dt
		if i.life <= 0 {
			i.give_back()
		}
	}
}

// give_back returns the node to its pool.
pub fn (mut i PoolItem) give_back() {
	if i.pool != unsafe { nil } {
		mut n := i.node
		i.pool.release(mut n)
	}
}

// release_node gives any pooled node back to the pool it came from.
pub fn release_node(n &core.Node) {
	mut item := n.get_component[PoolItem]() or { return }
	item.give_back()
}

// restart_particles replays the one-shot particle effects of a node and its children.
pub fn restart_particles(mut n core.Node) {
	if mut ps := n.get_component[render.ParticleSystem]() {
		ps.clear()
		ps.play()
	}
	for mut c in n.children {
		restart_particles(mut c)
	}
}
