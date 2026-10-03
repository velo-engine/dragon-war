module src

import math
import velo.core

// Game rules as plain data and pure functions (unit tested in game_test.v).

pub const max_level = 6 // a level 6 dragon is the top of the merge chain
pub const start_gold = 40
pub const start_lives = 10
pub const first_wave_delay = f32(5) // seconds before wave 1
pub const wave_gap = f32(6) // seconds between a cleared wave and the next
pub const spawn_y = f32(66) // monsters appear here (the top of the battlefield)
pub const wall_y = f32(520) // monsters that get this far hurt the city
pub const lane_min = f32(64)
pub const lane_max = f32(476)

pub struct DragonStats {
pub:
	name     string
	damage   f32
	cooldown f32 // seconds between fireballs
	splash   f32 // explosion radius (0 = hits one monster)
	speed    f32 // fireball speed
	scale    f32 // size of the fireball
	color    core.Color
}

pub fn clamp_level(level int) int {
	return if level < 1 {
		1
	} else if level > max_level {
		max_level
	} else {
		level
	}
}

pub fn dragon_stats(level int) DragonStats {
	i := clamp_level(level) - 1
	return DragonStats{
		name:     ['Hatchling', 'Frostling', 'Stormwing', 'Emberdrake', 'Sunlord', 'Inferno'][i]
		damage:   [f32(10), 26, 64, 160, 400, 1000][i]
		cooldown: [f32(0.9), 0.85, 0.8, 0.75, 0.7, 0.62][i]
		splash:   [f32(0), 0, 38, 50, 62, 78][i]
		speed:    [f32(520), 540, 560, 580, 600, 640][i]
		scale:    [f32(0.8), 0.9, 1.0, 1.15, 1.3, 1.5][i]
		color:    [core.rgba(150, 255, 110, 255), core.rgba(120, 205, 255, 255), core.rgba(205, 155, 255, 255),
			core.rgba(255, 130, 95, 255), core.rgba(255, 225, 100, 255), core.rgba(255, 110, 50, 255)][i]
	}
}

// dps: damage per second of one dragon (splash not counted).
pub fn (s DragonStats) dps() f32 {
	return s.damage / s.cooldown
}

// summon_cost grows with every dragon summoned so far.
pub fn summon_cost(summoned int) int {
	c := 10 + summoned * 2
	return if c > 90 { 90 } else { c }
}

pub struct EnemyStats {
pub:
	hp     f32
	speed  f32
	reward int // gold when killed
	leak   int // lives lost when it reaches the wall
}

pub fn enemy_stats(kind string) EnemyStats {
	return match kind {
		'imp' { EnemyStats{26, 78, 4, 1} }
		'orc' { EnemyStats{150, 34, 10, 2} }
		'demon' { EnemyStats{900, 24, 60, 5} }
		else { EnemyStats{36, 46, 4, 1} }
	}
}

pub const enemy_kinds = ['goblin', 'imp', 'orc', 'demon']

pub fn wave_hp_scale(wave int) f32 {
	return f32(math.pow(1.15, f64(wave - 1)))
}

pub fn wave_bonus(wave int) int {
	return 10 + 3 * wave
}

pub struct SpawnEvent {
pub:
	at   f32 // seconds after the wave started
	kind string
}

// wave_schedule lists what comes in a wave: goblins, imps from wave 2, orcs from wave 4, and a demon every fifth wave.
pub fn wave_schedule(wave int) []SpawnEvent {
	n := if 6 + wave * 2 > 44 { 44 } else { 6 + wave * 2 }
	gap := if f32(1.1) - f32(wave) * 0.04 < 0.5 { f32(0.5) } else { f32(1.1) - f32(wave) * 0.04 }
	mut out := []SpawnEvent{}
	for i in 0 .. n {
		mut kind := 'goblin'
		if wave >= 4 && i % 5 == 4 {
			kind = 'orc'
		} else if wave >= 2 && i % 3 == 2 {
			kind = 'imp'
		}
		out << SpawnEvent{f32(i) * gap, kind}
	}
	if wave % 5 == 0 {
		out << SpawnEvent{f32(n) * gap * 0.6, 'demon'}
		out.sort(a.at < b.at)
	}
	return out
}

pub fn clamp_f(v f32, lo f32, hi f32) f32 {
	return if v < lo {
		lo
	} else if v > hi {
		hi
	} else {
		v
	}
}
