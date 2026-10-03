"""Writes the prefabs and scenes (text) and the .meta files. Asset IDs are derived from the path, so they stay
stable between runs and a scene can refer to any asset with ref('sprites/spark.png')."""
import hashlib
import os

import layout
import rigs

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets")


def aid(path):
    return hashlib.md5(path.encode()).hexdigest()[:8]


def ref(path):
    return f'@asset("{aid(path)}")'


def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(text)


def meta(path, kind, **extra):
    lines = [f"id: {aid(path)}", f"kind: {kind}", "version: 1"]
    for k, v in sorted(extra.items()):
        lines.append(f"{k}: {v}")
    write(path + ".meta", "\n".join(lines) + "\n")


def v2(x, y):
    return f"[{x:g}, {y:g}]"


def col(c):
    return "[" + ", ".join(str(int(v)) for v in c) + "]"


DARK = (28, 32, 54, 245)
GREEN = (62, 168, 88, 255)
RED = (196, 70, 74, 255)
BLUE = (70, 120, 210, 255)
ORANGE = (230, 130, 40, 255)
GOLDC = (255, 224, 90, 255)
W, H = layout.W, layout.H


def label(text, size=20, color=(255, 255, 255, 255), align="center", valign="middle", extra=""):
    return (f'Label {{ text = "{text}"  size = {size}  align = "{align}"  valign = "{valign}"  color = {col(color)}'
            f'  shadow_color = [0, 0, 0, 150]  shadow_offset = [1, 2] {extra} }}')


def text_node(name, x, y, w, h, text, size=20, color=(255, 255, 255, 255), align="center", extra="", indent=4):
    p = " " * indent
    return (f"{p}node {name} {{\n{p}  position = {v2(x, y)}\n{p}  UITransform {{ size = {v2(w, h)} }}\n"
            f"{p}  {label(text, size, color, align, 'middle', extra)}\n{p}}}\n")


def button(name, x, y, w, h, text, color, size=20, indent=4, widget=""):
    p = " " * indent
    return (f"{p}node {name} {{\n{p}  position = {v2(x, y)}\n{p}  UITransform {{ size = {v2(w, h)} }}\n"
            + (f"{p}  {widget}\n" if widget else "")
            + f"{p}  Panel {{ color = {col(color)}  radius = 10  border_width = 1 }}\n{p}  Button {{ }}\n"
            + text_node("Text", 0, 0, w - 8, h - 4, text, size, indent=indent + 2)
            + f"{p}}}\n")


def sprite_node(name, x, y, w, h, path, indent=4, extra=""):
    p = " " * indent
    return (f"{p}node {name} {{\n{p}  position = {v2(x, y)}\n"
            f"{p}  Sprite {{ texture = {ref(path)}  size = {v2(w, h)} {extra} }}\n{p}}}\n")


def fullbleed(name, color, indent=2, block=True):
    p = " " * indent
    return (f"{p}node {name} {{\n{p}  position = {v2(W / 2, H / 2)}\n{p}  UITransform {{ size = {v2(W, H)} }}\n"
            f"{p}  Widget {{ align_left = true  align_right = true  align_top = true  align_bottom = true  safe_area = false }}\n"
            f"{p}  Panel {{ color = {col(color)}{'' if block else '  block_input = false'} }}\n{p}}}\n")


# ---------- prefabs ----------

def enemy_prefab(kind):
    parts = rigs.enemy_parts(kind)
    sc = rigs.ENEMIES[kind]["scale"]
    top = min(p.pos[1] - p.pivot[1] for p in parts)
    feet = max(p.pos[1] + p.img.h - p.pivot[1] for p in parts if p.name.startswith("leg"))
    half_w = max(p.img.w for p in parts if p.name == "body") / 2
    bar_w = max(34, half_w * 2 * sc * 1.4)
    write(f"prefabs/enemy_{kind}.scene", f"""# {kind}: a Kine2D skeleton (characters/{kind}.*) that marches down the field. Enemy comes from src/enemy.v;
# the Game keeps these nodes in a pool, so they are created once and reused.
node Enemy{kind.capitalize()} {{
  Enemy {{ kind = "{kind}" }}
  node Shadow {{
    position = {v2(0, feet * sc - 3)}
    Sprite {{ texture = {ref('sprites/shadow.png')}  size = {v2(half_w * 2 * sc * 1.5, 12 * sc + 4)} }}
  }}
  node Body {{
    scale = {v2(sc, sc)}
    Kine2D {{ data = {ref(f'characters/{kind}.skel.json')}  atlas = {ref(f'characters/{kind}.atlas.json')}  animation = "walk" }}
  }}
  node Bar {{
    position = {v2(0, top * sc - 9)}
    UITransform {{ size = {v2(bar_w, 6)} }}
    ProgressBar {{ progress = 1  fill_color = [96, 220, 112, 255]  back_color = [24, 14, 30, 210]  radius = 3 }}
  }}
}}
""")


def dragon_prefab():
    write("prefabs/dragon.scene", f"""# A dragon. Dragon (src/dragon.v) swaps the Kine2D files of Body to the ones of its level (characters/dragon1..6),
# so one prefab (and one pool) serves every level.
node Dragon {{
  Dragon {{ }}
  node Shadow {{
    position = [0, 36]
    Sprite {{ texture = {ref('sprites/shadow.png')}  size = [70, 22] }}
  }}
  node Body {{
    position = [0, 10]
    scale = [0.85, 0.85]
    Kine2D {{ data = {ref('characters/dragon1.skel.json')}  atlas = {ref('characters/dragon1.atlas.json')}  animation = "idle" }}
  }}
  node Badge {{
    position = [-31, -36]
    UITransform {{ size = [30, 20] }}
    Panel {{ color = [24, 18, 44, 215]  radius = 9  border_width = 1  border_color = [255, 224, 120, 220]  block_input = false }}
    node Text {{
      UITransform {{ size = [30, 20] }}
      Label {{ text = "1"  size = 15  align = "center"  valign = "middle"  color = [255, 230, 130, 255] }}
    }}
  }}
}}
""")


def bullet_prefab():
    write("prefabs/bullet.scene", f"""# A dragon fireball. Projectile (src/projectile.v) flies it to its target; Game pools these nodes.
node Bullet {{
  Projectile {{ }}
  node Trail {{
    ParticleSystem {{ texture = {ref('sprites/spark.png')}  rate = 46  looping = true  lifetime = 0.28  speed = 8  spread = 180  start_size = 16  end_size = 2
      additive = true  max_particles = 24  start_color = [255, 200, 90, 220]  end_color = [255, 90, 30, 0] }}
  }}
  Sprite {{ texture = {ref('sprites/fireball.png')}  size = [44, 30] }}
}}
""")


def particles(texture, **kw):
    f = {"texture": ref(texture), "rate": 0, "looping": "false", "duration": 0, "additive": "true"}
    f.update(kw)
    return "ParticleSystem { " + "  ".join(f"{k} = {v}" for k, v in f.items()) + " }"


def fx_prefabs():
    spark = "sprites/spark.png"
    write("prefabs/fx_hit.scene", "node FxHit {\n  " + particles(spark, burst=8, lifetime=0.26, speed=120, speed_var=40, spread=180, damping=3,
          start_size=11, end_size=2, start_color=col((255, 236, 160, 255)), end_color=col((255, 120, 40, 0))) + "\n}\n")
    write("prefabs/fx_boom.scene", "node FxBoom {\n  " + particles(spark, burst=16, lifetime=0.6, speed=70, speed_var=40, spread=180, damping=2.5,
          start_size=30, end_size=10, additive="false", start_color=col((70, 60, 60, 190)), end_color=col((40, 40, 40, 0))) + "\n  node Fire {\n    "
          + particles(spark, burst=24, lifetime=0.42, speed=170, speed_var=60, spread=180, damping=3, start_size=26, end_size=6,
                      start_color=col((255, 220, 120, 255)), end_color=col((255, 70, 20, 0))) + "\n  }\n}\n")
    write("prefabs/fx_die.scene", "node FxDie {\n  " + particles(spark, burst=12, lifetime=0.5, speed=70, speed_var=30, spread=180, damping=2.5,
          start_size=20, end_size=5, additive="false", start_color=col((235, 235, 235, 220)), end_color=col((200, 200, 200, 0))) + "\n}\n")
    write("prefabs/fx_merge.scene", "node FxMerge {\n  " + particles(spark, burst=26, lifetime=0.7, speed=170, speed_var=50, spread=180, damping=2.6,
          start_size=18, end_size=3, start_color=col((255, 236, 140, 255)), end_color=col((255, 150, 40, 0)))
          + "\n  node Ring {\n    " + particles(spark, burst=14, lifetime=0.5, speed=60, speed_var=20, spread=180, damping=2, shape='"circle"', shape_size=v2(26, 0),
                                                start_size=22, end_size=4, start_color=col((255, 255, 255, 230)), end_color=col((140, 220, 255, 0))) + "\n  }\n}\n")
    write("prefabs/fx_summon.scene", "node FxSummon {\n  " + particles(spark, burst=14, lifetime=0.5, speed=80, speed_var=30, spread=180, damping=3,
          shape='"circle"', shape_size=v2(20, 0), start_size=16, end_size=4, additive="false",
          start_color=col((240, 230, 200, 230)), end_color=col((220, 200, 160, 0))) + "\n}\n")
    write("prefabs/floating_text.scene", """node FloatingText {
  FloatText { }
  UITransform { size = [110, 28] }
  Label { text = ""  size = 24  align = "center"  valign = "middle"  outline_color = [20, 10, 30, 255]  outline_width = 2.5 }
}
""")


SFX = ["fire", "hit", "explode", "die", "coin", "summon", "merge", "leak", "wave", "win", "lose", "click", "deny"]
VOLUME = {"fire": 0.3, "hit": 0.3, "explode": 0.6, "die": 0.35, "coin": 0.5, "summon": 0.7, "merge": 0.7, "leak": 0.7, "wave": 0.6,
          "win": 0.8, "lose": 0.8, "click": 0.5, "deny": 0.5}


def audio_prefab():
    lines = ["# Music and sound effects, shared by the title screen and the game (`persistent`: the music keeps playing",
             "# when the scene changes). src/util.v plays them by name: play_sfx(scene, 'fire', pitch).", "node Audio {", "  persistent = true",
             f'  node Music {{ AudioSource {{ clip = {ref("sounds/music.wav")}  looping = true  bus = "music"  volume = 0.3 }} }}']
    for s in SFX:
        bus = "ui" if s in ("click", "deny") else "sfx"
        lines.append(f'  node {s} {{ AudioSource {{ clip = {ref(f"sounds/{s}.wav")}  play_on_start = false  bus = "{bus}"  volume = {VOLUME[s]} }} }}')
    lines.append("}")
    write("prefabs/audio.scene", "\n".join(lines) + "\n")


def hud_prefab():
    top_item = lambda name, left, icon, text_w: (
        f"    node {name} {{\n      UITransform {{ size = [{text_w + 34}, 32] }}\n"
        f"      Widget {{ align_left = true  left = {left}  align_center_y = true }}\n"
        + sprite_node("Icon", -text_w / 2 - 2, 0, 26, 26, icon, 6)
        + text_node("Text", 17, 0, text_w, 32, "0", 22, align="left", indent=6) + "    }\n")
    write("prefabs/hud.scene", f"""# The on-screen UI. Hud (src/hud.v) reads the Game and handles every button here. The node has `unscaled_time`
# so the buttons keep working while the game is paused.
node HUD {{
  unscaled_time = true
  Canvas {{ }}
  Hud {{ }}
  node TopBg {{
    position = [{W / 2}, 28]
    UITransform {{ size = [{W}, 56] }}
    Widget {{ align_left = true  align_right = true  align_top = true  safe_area = false }}
    Panel {{ color = [20, 24, 44, 235] }}
  }}
  node Top {{
    UITransform {{ size = [{W}, 56] }}
    Widget {{ align_left = true  align_right = true  align_top = true }}
{top_item('Lives', 8, 'sprites/icon_heart.png', 36)}{top_item('Gold', 112, 'sprites/icon_coin.png', 62)}{top_item('Wave', 232, 'sprites/icon_wave.png', 96)}
{button('Speed', 0, 0, 54, 34, 'x1', BLUE, 18, 4, 'Widget { align_right = true  right = 68  align_center_y = true }')}
    node Pause {{
      UITransform {{ size = [54, 34] }}
      Widget {{ align_right = true  right = 8  align_center_y = true }}
      Panel {{ color = {col(BLUE)}  radius = 10  border_width = 1 }}
      Button {{ }}
      node Icon {{
        Sprite {{ texture = {ref('sprites/icon_pause.png')}  size = [22, 22] }}
      }}
    }}
  }}
  node Summon {{
    position = [{W / 2}, {layout.SUMMON_Y}]
    UITransform {{ size = [330, 60] }}
    Panel {{ color = {col(ORANGE)}  radius = 16  border_width = 2  border_color = [255, 235, 180, 200] }}
    Button {{ }}
{sprite_node('Egg', -132, 0, 42, 42, 'sprites/icon_egg.png', 4)}{text_node('Text', -26, 0, 150, 40, 'SUMMON', 26, extra='outline_color = [90, 40, 10, 255]  outline_width = 2', indent=4)}{sprite_node('Coin', 74, 0, 28, 28, 'sprites/icon_coin.png', 4)}{text_node('Cost', 120, 0, 70, 40, '10', 26, GOLDC, 'left', indent=4)}  }}
  node Hint {{
    active = false
    position = [{W / 2}, 500]
    UITransform {{ size = [500, 56] }}
    Label {{ text = ""  size = 21  align = "center"  valign = "middle"  wrap = true  outline_color = [20, 10, 30, 255]  outline_width = 2.5 }}
  }}
  node Banner {{
    active = false
    position = [{W / 2}, 250]
    UITransform {{ size = [500, 90] }}
    Label {{ text = ""  size = 60  align = "center"  valign = "middle"  color = [255, 236, 150, 255]  outline_color = [110, 50, 10, 255]  outline_width = 4 }}
  }}
  node Overlay {{
    active = false
    z_index = 20
    position = [{W / 2}, {H / 2}]
    UITransform {{ size = [{W}, {H}] }}
    Widget {{ align_left = true  align_right = true  align_top = true  align_bottom = true  safe_area = false }}
    Panel {{ color = [8, 8, 20, 170] }}
    node Box {{
      UITransform {{ size = [440, 330] }}
      Widget {{ align_center_x = true  align_center_y = true }}
      Panel {{ color = {col(DARK)}  radius = 16  border_width = 2  border_color = [255, 255, 255, 60] }}
{text_node('Title', 0, -128, 400, 56, 'Paused', 44, GOLDC, extra='outline_color = [60, 30, 10, 255]  outline_width = 2.5')}{text_node('Sub', 0, -72, 400, 52, '', 19, (220, 228, 245, 255), extra='wrap = true')}{button('Resume', 0, -4, 270, 48, 'Resume', GREEN, 22)}{button('Restart', 0, 56, 270, 48, 'Restart', BLUE, 22)}{button('Menu', 0, 116, 270, 48, 'Main menu', (110, 100, 130, 255), 22)}    }}
  }}
}}
""")


def cells(names, xs, y, tex, indent=6):
    p = " " * indent
    out = ""
    for i, x in enumerate(xs):
        out += (f"{p}node {names}{i} {{\n{p}  position = {v2(x, y)}\n{p}  Sprite {{ texture = {ref(tex)} }}\n"
                f"{p}  node Hi {{\n{p}    active = false\n{p}    z_index = 1\n{p}    Sprite {{ texture = {ref('sprites/slot_hi.png')} }}\n{p}  }}\n{p}}}\n")
    return out


def main_scene():
    slots = ""
    for r, y in enumerate(layout.SLOT_ROWS):
        slots += cells(f"S{r}_", layout.SLOT_X, y, "sprites/slot.png")
    write("scenes/main.scene", f"""# The game. Board/Slots are the battle slots (dragons there attack), Board/Bench is where new dragons wait.
# Game (src/game.v) reads the cell positions from these nodes, so the layout can be changed in the editor.
node Main {{
  node Audio from {ref('prefabs/audio.scene')} {{ }}
{fullbleed('Background', (36, 30, 62, 255), block=False)}  node Board {{
    node Field {{
      position = {v2(W / 2, layout.TOP + layout.FIELD_H / 2)}
      Sprite {{ texture = {ref('sprites/field.png')} }}
    }}
    node Floor {{
      position = {v2(W / 2, 560 + (H - 560) / 2)}
      Sprite {{ texture = {ref('sprites/floor.png')} }}
    }}
    node Enemies {{
      y_sort = true
    }}
    node Wall {{
      position = {v2(W / 2, layout.WALL_Y)}
      Sprite {{ texture = {ref('sprites/wall.png')} }}
    }}
    node Slots {{
{slots}    }}
    node Bench {{
{cells('B', layout.SLOT_X, layout.BENCH_Y, 'sprites/bench.png')}    }}
    node Dragons {{
      y_sort = true
    }}
    node Bullets {{
      z_index = 2
    }}
    node Fx {{
      z_index = 3
    }}
  }}
  node Game {{
    Game {{ }}
  }}
  node HUD from {ref('prefabs/hud.scene')} {{ }}
}}
""")


def menu_scene():
    dragons = ""
    for i, (lv, x, y, s) in enumerate([(2, 112, 540, 1.5), (6, 270, 500, 2.3), (4, 428, 540, 1.5)]):
        dragons += (f"  node Dragon{i} {{\n    position = {v2(x, y)}\n    scale = {v2(s, s)}\n"
                    f"    Kine2D {{ data = {ref(f'characters/dragon{lv}.skel.json')}  atlas = {ref(f'characters/dragon{lv}.atlas.json')}  animation = \"idle\"  speed = {0.9 + 0.1 * i:g} }}\n  }}\n")
    write("scenes/menu.scene", f"""# Title screen: MenuScreen (src/menu.v) starts the game and shows the best result.
node Menu {{
  node Audio from {ref('prefabs/audio.scene')} {{ }}
{fullbleed('Sky', (92, 70, 150, 255), block=False)}  node Background {{
    position = {v2(W / 2, H / 2)}
    Sprite {{ texture = {ref('sprites/menu_bg.png')}  size = [{W}, {H}] }}
  }}
{dragons}  node UI {{
    Canvas {{ }}
    MenuScreen {{ }}
    node Title {{
      position = [{W / 2}, 150]
      UITransform {{ size = [520, 150] }}
      Label {{ text = "DRAGON\\nCITY"  size = 72  align = "center"  valign = "middle"  color = [255, 236, 150, 255]  line_spacing = 1.0
              outline_color = [110, 50, 10, 255]  outline_width = 4  shadow_color = [0, 0, 0, 120]  shadow_offset = [4, 6] }}
    }}
    node Tagline {{
      position = [{W / 2}, 258]
      UITransform {{ size = [520, 34] }}
      Label {{ text = "Merge dragons, defend the city"  size = 24  align = "center"  valign = "middle"  outline_color = [60, 30, 80, 255]  outline_width = 2 }}
    }}
    node Best {{
      position = [{W / 2}, 298]
      UITransform {{ size = [520, 32] }}
      Label {{ text = ""  size = 20  align = "center"  valign = "middle"  outline_color = [60, 30, 80, 255]  outline_width = 2 }}
    }}
    node Play {{
      position = [{W / 2}, 740]
      UITransform {{ size = [280, 74] }}
      Panel {{ color = [64, 176, 92, 255]  radius = 16  border_width = 2 }}
      Button {{ }}
      node Text {{ Label {{ text = "PLAY"  size = 38  align = "center"  valign = "middle"  outline_color = [20, 70, 30, 255]  outline_width = 2 }} }}
    }}
  }}
}}
""")


def write_all_prefabs():
    for k in rigs.ENEMIES:
        enemy_prefab(k)
    dragon_prefab()
    bullet_prefab()
    fx_prefabs()
    audio_prefab()
    hud_prefab()
    main_scene()
    menu_scene()
    for p in (["audio", "hud", "dragon", "bullet", "floating_text", "fx_hit", "fx_boom", "fx_die", "fx_merge", "fx_summon"]
              + [f"enemy_{k}" for k in rigs.ENEMIES]):
        meta(f"prefabs/{p}.scene", "scene")
    meta("scenes/main.scene", "scene")
    meta("scenes/menu.scene", "scene")
