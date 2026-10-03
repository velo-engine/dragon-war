# Dragon City

Portrait merge-and-defend game on the [Velo](../../github/velo) engine. Monsters march down the field; dragons stand in the
slots below the wall and breathe fire at them. Summon dragons onto the bench, **drag them up into the battle slots**, and
**drag two dragons of the same level onto each other** to merge them into a stronger one (6 levels).

```bash
velo run                 # desktop window (mouse = finger)
velo run ios-sim         # or: velo run android
DC_AUTO=1 velo run       # a bot plays by itself (skips the menu): handy to watch pooling / waves
VMODULES=<folder holding the velo repo> v test src/
python3 tools/gen_assets.py   # regenerates everything under assets/ (pure Python)
```

- **Kine2D**: six dragon rigs (`idle`, `attack`: head lunge, wing flap, flame) and four monsters (`walk`, `die`) in `assets/characters/`.
  A dragon switches rig on merge by assigning the new `.skel.json/.atlas.json` to its `Kine2D` (`src/dragon.v`).
- **Pools** (`src/pool.v`): monsters (one pool per kind), fireballs, dragons, effects and floating texts are created once
  (prewarmed in `Game.start`) and switched on/off; a fireball checks `Enemy.uid` so a recycled monster is never hit by mistake.
- Layout is read from the scene: move `Board/Slots` and `Board/Bench` cells in `velo editor`.
