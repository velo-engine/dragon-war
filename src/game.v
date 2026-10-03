module src

import math
import os
import velo.core
import velo.render

pub enum Phase {
	playing
	lost
}

// Cell — one spot a dragon can stand on: a battle slot (the dragon shoots) or a bench cell (it waits).
pub struct Cell {
pub mut:
	pos    core.Vec2
	battle bool
	dragon &Dragon = unsafe { nil }
	hi     &core.Node = unsafe { nil } // the highlight child, shown while dragging
}

// Game — the rules: summoning, drag and drop, merging, waves, gold and lives. It lives on the "Game" node of
// scenes/main.scene; Hud reads its state and calls summon(); monsters, fireballs and dragons report back to it.
// Monsters, fireballs, dragons, effects and texts all come from Pools made in start().
pub struct Game {
	core.Component
pub mut:
	gold      int   @[hide]
	lives     int   @[hide]
	wave      int   @[hide] // waves started so far
	phase     Phase @[hide]
	countdown f32   @[hide] // seconds until the next wave
	wave_time f32   @[hide]
	schedule  []SpawnEvent @[hide]
	next_event int  @[hide]
	in_wave   bool  @[hide]
	summoned  int   @[hide]
	kills     int   @[hide]
	top_level int = 1 @[hide] // highest dragon level reached this game
	uid_next  int   @[hide]
	cells     []Cell    @[hide]
	enemies   []&Enemy  @[hide] // the monsters that are alive right now
	enemy_pools map[string]&Pool @[hide]
	fx_pools    map[string]&Pool @[hide]
	bullets   &Pool = unsafe { nil } @[hide]
	dragons   &Pool = unsafe { nil } @[hide]
	texts     &Pool = unsafe { nil } @[hide]
	drag      &Dragon = unsafe { nil } @[hide] // the dragon under the finger
	drag_from int      @[hide]
	drag_off  core.Vec2 @[hide]
	hint      string   @[hide]
	hint_time f32      @[hide]
	banner    string   @[hide]
	banner_time f32    @[hide]
	pulse     f32      @[hide]
	auto_t    f32      @[hide]
}

pub fn (mut g Game) start() {
	g.gold = start_gold
	g.lives = start_lives
	g.phase = .playing
	g.countdown = first_wave_delay
	g.top_level = 1
	g.read_cells()
	g.make_pools()
	g.say('Summon dragons, drag two alike together to merge them', 6)
}

fn (mut g Game) read_cells() {
	sc := g.scene()
	g.cells = []Cell{}
	for path, battle in {
		'Board/Slots': true
		'Board/Bench': false
	} {
		parent := sc.find(path) or { panic('scenes/main.scene needs a ${path} node') }
		for c in parent.children {
			g.cells << Cell{
				pos:    c.position
				battle: battle
				hi:     c.find('Hi') or { unsafe { nil } }
			}
		}
	}
}

fn (mut g Game) make_pools() {
	mut sc := g.scene()
	enemies := sc.find('Board/Enemies') or { panic('scenes/main.scene needs Board/Enemies') }
	bullets := sc.find('Board/Bullets') or { panic('scenes/main.scene needs Board/Bullets') }
	dragons := sc.find('Board/Dragons') or { panic('scenes/main.scene needs Board/Dragons') }
	fx := sc.find('Board/Fx') or { panic('scenes/main.scene needs Board/Fx') }
	for kind, n in {
		'goblin': 20
		'imp':    14
		'orc':    8
		'demon':  2
	} {
		mut p := new_pool('prefabs/enemy_${kind}.scene', enemies)
		p.prewarm(mut sc, n)
		g.enemy_pools[kind] = p
	}
	g.bullets = new_pool('prefabs/bullet.scene', bullets)
	g.bullets.prewarm(mut sc, 40)
	g.dragons = new_pool('prefabs/dragon.scene', dragons)
	g.dragons.prewarm(mut sc, 6)
	g.texts = new_pool('prefabs/floating_text.scene', fx)
	g.texts.prewarm(mut sc, 10)
	for name, n in {
		'hit':    12
		'boom':   6
		'die':    8
		'merge':  3
		'summon': 3
	} {
		mut p := new_pool('prefabs/fx_${name}.scene', fx)
		p.prewarm(mut sc, n)
		g.fx_pools[name] = p
	}
}

pub fn (g &Game) running() bool {
	return g.phase == .playing
}

pub fn (mut g Game) say(text string, seconds f32) {
	g.hint = text
	g.hint_time = seconds
}

fn (mut g Game) announce(text string) {
	g.banner = text
	g.banner_time = 1.8
}

pub fn (mut g Game) update(dt f32) {
	g.pulse += dt
	if g.hint_time > 0 {
		g.hint_time -= dt
	}
	if g.banner_time > 0 {
		g.banner_time -= dt
	}
	g.handle_drag()
	if auto_play && g.phase == .playing {
		g.auto_step(dt)
	}
	if g.phase == .playing {
		g.run_waves(dt)
	}
	g.refresh_cells()
}

// ---------- waves ----------

fn (mut g Game) run_waves(dt f32) {
	if !g.in_wave {
		g.countdown -= dt
		if g.countdown <= 0 {
			g.start_wave()
		}
		return
	}
	g.wave_time += dt
	for g.next_event < g.schedule.len && g.schedule[g.next_event].at <= g.wave_time {
		g.spawn_enemy(g.schedule[g.next_event].kind)
		g.next_event++
	}
	if g.next_event >= g.schedule.len && g.enemies.len == 0 {
		g.wave_cleared()
	}
}

fn (mut g Game) start_wave() {
	g.wave++
	g.schedule = wave_schedule(g.wave)
	g.next_event = 0
	g.wave_time = 0
	g.in_wave = true
	g.announce(if g.wave % 5 == 0 { 'WAVE ${g.wave}\nBOSS!' } else { 'WAVE ${g.wave}' })
	play_sfx(g.scene(), 'wave', 1)
}

fn (mut g Game) wave_cleared() {
	bonus := wave_bonus(g.wave)
	g.gold += bonus
	g.in_wave = false
	g.countdown = wave_gap
	g.say('Wave ${g.wave} cleared  +${bonus} gold', 3)
	play_sfx(g.scene(), 'coin', 1)
	g.record()
}

fn (mut g Game) spawn_enemy(kind string) {
	mut sc := g.scene()
	mut pool := g.enemy_pools[kind] or { return }
	mut n := pool.acquire(mut sc, 0) or { return }
	mut e := n.get_component[Enemy]() or { return }
	g.uid_next++
	e.spawn(g, g.uid_next, g.wave)
	g.enemies << e
}

// front_enemy: the monster closest to the wall, which every dragon aims at.
pub fn (g &Game) front_enemy() ?&Enemy {
	mut best := unsafe { &Enemy(nil) }
	for e in g.enemies {
		if !e.alive {
			continue
		}
		if best == unsafe { nil } || e.node.position.y > best.node.position.y {
			best = unsafe { e }
		}
	}
	if best == unsafe { nil } {
		return none
	}
	return best
}

fn (mut g Game) forget(e &Enemy) {
	for i, x in g.enemies {
		if x.uid == e.uid {
			g.enemies.delete(i)
			return
		}
	}
}

// fire takes a fireball from the pool and sends it at `target`.
pub fn (mut g Game) fire(from core.Vec2, target &Enemy, st DragonStats) {
	mut sc := g.scene()
	mut n := g.bullets.acquire(mut sc, 0) or { return }
	mut p := n.get_component[Projectile]() or { return }
	p.launch(g, from, target, st)
}

pub fn (mut g Game) spawn_fx(name string, at core.Vec2) {
	mut sc := g.scene()
	mut pool := g.fx_pools[name] or { return }
	mut n := pool.acquire(mut sc, 1.2) or { return }
	n.position = at
	restart_particles(mut n)
}

pub fn (mut g Game) float_text(text string, at core.Vec2, color core.Color) {
	mut sc := g.scene()
	mut n := g.texts.acquire(mut sc, 1.0) or { return }
	mut f := n.get_component[FloatText]() or { return }
	f.launch(text, at, color)
}

pub fn (mut g Game) on_kill(e &Enemy) {
	g.forget(e)
	g.gold += e.reward
	g.kills++
	at := e.node.position
	g.spawn_fx('die', at)
	g.float_text('+${e.reward}', at + core.vec2(0, -26), core.rgba(255, 224, 90, 255))
	play_sfx(g.scene(), 'die', 0.9 + f32(e.reward % 5) * 0.04)
}

pub fn (mut g Game) on_leak(e &Enemy, n int) {
	g.forget(e)
	g.lives -= n
	g.float_text('-${n}', core.vec2(e.node.position.x, wall_y - 30), core.rgba(255, 90, 90, 255))
	play_sfx(g.scene(), 'leak', 1)
	if g.lives <= 0 {
		g.lives = 0
		g.lose()
	}
}

fn (mut g Game) lose() {
	if g.phase == .lost {
		return
	}
	g.phase = .lost
	g.cancel_drag()
	g.record()
	play_sfx(g.scene(), 'lose', 1)
}

// record keeps the best result in the save data (shown on the title screen).
fn (mut g Game) record() {
	mut st := g.scene().store
	reached := if g.in_wave { g.wave - 1 } else { g.wave }
	if reached > st.get_int('best_wave', 0) {
		st.set_int('best_wave', reached)
	}
	if g.top_level > st.get_int('best_dragon', 0) {
		st.set_int('best_dragon', g.top_level)
	}
}

// ---------- summoning ----------

pub fn (g &Game) summon_cost() int {
	return summon_cost(g.summoned)
}

// summon_cell: a free bench cell, else a free battle slot, else -1.
fn (g &Game) free_cell() int {
	for pass in [false, true] {
		for i, c in g.cells {
			if c.battle == pass && c.dragon == unsafe { nil } && (g.drag == unsafe { nil } || g.drag_from != i) {
				return i
			}
		}
	}
	return -1
}

pub fn (mut g Game) summon() {
	if g.phase != .playing {
		return
	}
	mut sc := g.scene()
	cost := g.summon_cost()
	if g.gold < cost {
		g.say('Not enough gold (${cost} needed)', 2)
		play_sfx(sc, 'deny', 1)
		return
	}
	i := g.free_cell()
	if i < 0 {
		g.say('No room! Merge dragons to make space', 2.4)
		play_sfx(sc, 'deny', 1)
		return
	}
	g.gold -= cost
	g.summoned++
	mut n := g.dragons.acquire(mut sc, 0) or { return }
	mut d := n.get_component[Dragon]() or { return }
	d.setup(g, 1, i, g.cells[i].pos)
	g.place(mut d, i)
	g.spawn_fx('summon', g.cells[i].pos)
	play_sfx(sc, 'summon', 1)
}

// place puts a dragon on a cell (the cell must be free).
fn (mut g Game) place(mut d Dragon, i int) {
	g.cells[i].dragon = d
	d.cell = i
	d.home = g.cells[i].pos
	d.battle = g.cells[i].battle
	d.dragged = false
	d.node.z_index = 0
}

// ---------- drag and drop ----------

// cell_at: the cell under `p`, or -1.
fn (g &Game) cell_at(p core.Vec2) int {
	half := f32(54)
	for i, c in g.cells {
		if p.x >= c.pos.x - half && p.x <= c.pos.x + half && p.y >= c.pos.y - half && p.y <= c.pos.y + half {
			return i
		}
	}
	return -1
}

fn (mut g Game) handle_drag() {
	inp := g.input()
	sc := g.scene()
	if g.drag == unsafe { nil } {
		if g.phase == .playing && inp.mouse_pressed && !render.pointer_over_ui(sc, inp.mouse) {
			i := g.cell_at(inp.mouse)
			if i >= 0 && g.cells[i].dragon != unsafe { nil } {
				g.begin_drag(i)
			}
		}
		return
	}
	// the dragon is lifted a little above the finger so it stays visible
	g.drag.node.position = inp.mouse + g.drag_off
	if !inp.mouse_down || inp.mouse_released {
		g.drop()
	}
}

fn (mut g Game) begin_drag(i int) {
	mut d := g.cells[i].dragon
	g.cells[i].dragon = unsafe { nil }
	g.drag = d
	g.drag_from = i
	g.drag_off = core.vec2(0, -26) + (d.node.position - g.input().mouse).mul(0.4)
	d.dragged = true
	d.node.z_index = 40
	d.pop = 0
	play_sfx(g.scene(), 'click', 1.3)
}

fn (mut g Game) cancel_drag() {
	if g.drag == unsafe { nil } {
		return
	}
	mut d := g.drag
	g.drag = unsafe { nil }
	g.place(mut d, g.drag_from)
}

fn (mut g Game) drop() {
	mut d := g.drag
	from := g.drag_from
	g.drag = unsafe { nil }
	to := g.cell_at(d.node.position)
	if to < 0 || to == from {
		g.place(mut d, from)
		return
	}
	mut t := g.cells[to].dragon
	if t == unsafe { nil } {
		g.place(mut d, to)
		play_sfx(g.scene(), 'click', 0.9)
		return
	}
	if t.level == d.level && d.level < max_level {
		g.merge(mut d, mut t)
		return
	}
	// different dragons trade places
	g.cells[to].dragon = unsafe { nil }
	g.place(mut t, from)
	g.place(mut d, to)
	play_sfx(g.scene(), 'click', 0.9)
}

// merge: `d` (the dragged one) joins `t`; `t` stays and levels up, `d` goes back to the pool.
fn (mut g Game) merge(mut d Dragon, mut t Dragon) {
	mut sc := g.scene()
	d.dragged = false
	mut node := d.node
	g.dragons.release(mut node)
	t.set_level(t.level + 1)
	t.pop = 1
	at := g.cells[t.cell].pos
	g.spawn_fx('merge', at)
	st := dragon_stats(t.level)
	g.float_text(st.name, at + core.vec2(0, -52), st.color)
	play_sfx(sc, 'merge', 0.9 + f32(t.level) * 0.05)
	if t.level > g.top_level {
		g.top_level = t.level
		g.announce('${st.name}!')
		g.say('New dragon: ${st.name} (damage ${int(st.damage)})', 3)
	}
}

// refresh_cells lights up the cell under the dragged dragon: green = move there, gold = merge, and a soft glow on every
// dragon it could merge with.
fn (mut g Game) refresh_cells() {
	mut hover := -1
	if g.drag != unsafe { nil } {
		hover = g.cell_at(g.drag.node.position)
	}
	for i in 0 .. g.cells.len {
		mut c := g.cells[i]
		if c.hi == unsafe { nil } {
			continue
		}
		mut hi := c.hi
		if g.drag == unsafe { nil } {
			hi.active = false
			continue
		}
		mergeable := c.dragon != unsafe { nil } && c.dragon.level == g.drag.level && g.drag.level < max_level
		hi.active = i == hover || mergeable
		if mut s := hi.get_component[render.Sprite]() {
			s.color = if mergeable {
				core.rgba(255, 220, 90, if i == hover { u8(255) } else { u8(150 + 70 * f32(math.fmod(f64(g.pulse * 6), 1.0))) })
			} else if i == g.drag_from {
				core.rgba(255, 255, 255, 120)
			} else {
				core.rgba(120, 255, 140, 230)
			}
		}
	}
}

// ---------- pause / speed / restart ----------

pub fn (mut g Game) toggle_pause() {
	mut sc := g.scene()
	sc.paused = !sc.paused
}

pub fn (mut g Game) toggle_speed() {
	mut sc := g.scene()
	sc.time_scale = if sc.time_scale > 1 { f32(1) } else { f32(2) }
}

pub fn (mut g Game) restart() {
	mut sc := g.scene()
	sc.paused = false
	sc.time_scale = 1
	sc.reload()
}

pub fn (mut g Game) to_menu() {
	mut sc := g.scene()
	sc.paused = false
	sc.time_scale = 1
	sc.change_scene('scenes/menu.scene', fade: 0.35)
}

// ---------- self-play (DC_AUTO=1): a tiny bot that summons, moves and merges, to watch the game run without hands ----------

const auto_play = os.getenv('DC_AUTO') != ''

fn (mut g Game) auto_step(dt f32) {
	g.auto_t += dt
	if g.auto_t < 0.35 || g.drag != unsafe { nil } {
		return
	}
	g.auto_t = 0
	// merge any pair of the same level
	for i in 0 .. g.cells.len {
		for j in i + 1 .. g.cells.len {
			mut a := g.cells[i].dragon
			mut b := g.cells[j].dragon
			if a != unsafe { nil } && b != unsafe { nil } && a.level == b.level && a.level < max_level {
				g.cells[j].dragon = unsafe { nil }
				g.merge(mut b, mut a)
				return
			}
		}
	}
	// bench -> free battle slot
	for i, c in g.cells {
		if !c.battle && c.dragon != unsafe { nil } {
			for j, s in g.cells {
				if s.battle && s.dragon == unsafe { nil } {
					mut d := c.dragon
					g.cells[i].dragon = unsafe { nil }
					g.place(mut d, j)
					return
				}
			}
		}
	}
	if g.gold >= g.summon_cost() {
		g.summon()
	}
}
