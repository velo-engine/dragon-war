module src

fn test_dragon_stats_grow_with_level() {
	for l in 1 .. max_level {
		assert dragon_stats(l + 1).damage > 2 * dragon_stats(l).damage // merging two is always worth it
	}
	assert dragon_stats(0).name == dragon_stats(1).name
	assert dragon_stats(99).name == dragon_stats(max_level).name
}

fn test_summon_cost_grows_and_caps() {
	assert summon_cost(0) == 10
	assert summon_cost(5) == 20
	assert summon_cost(1000) == 90
}

fn test_wave_schedule() {
	w1 := wave_schedule(1)
	assert w1.len == 8
	assert w1.all(it.kind == 'goblin')
	assert wave_schedule(2).any(it.kind == 'imp')
	assert wave_schedule(4).any(it.kind == 'orc')
	assert !wave_schedule(4).any(it.kind == 'demon')
	assert wave_schedule(5).any(it.kind == 'demon')
	for w in [1, 7, 30] {
		s := wave_schedule(w)
		for i in 1 .. s.len {
			assert s[i].at >= s[i - 1].at // sorted by time
		}
	}
}

fn test_hp_scale() {
	assert wave_hp_scale(1) == 1
	assert wave_hp_scale(10) > wave_hp_scale(5)
}
