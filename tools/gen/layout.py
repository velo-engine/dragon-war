"""The board layout in design units (540x960), shared by the art painter (art.py) and the scene writer (scenes.py).
The V code reads the cell positions back out of the scene (Board/Slots, Board/Bench), so there is no second copy there."""
W, H = 540, 960
TOP = 56                      # HUD bar height; the battlefield starts under it
FIELD_H = 504                 # battlefield: y 56 .. 560
WALL_Y = 548                  # enemies that get this far hurt the city
CELL = 96
SLOT_X = [54 + 108 * i for i in range(5)]
SLOT_ROWS = [622, 722]        # the two rows of battle slots
BENCH_Y = 900                 # the bench: dragons wait here until they are dragged up
SUMMON_Y = 814                # the summon button
