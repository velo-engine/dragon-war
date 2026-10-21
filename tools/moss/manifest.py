"""Every picture MOSS renders: name, generation size and prompt. Cut-outs are painted on plain white and cut out later."""
from dataclasses import dataclass

STYLE = ("cute casual mobile game character art, soft rounded shapes, thick dark outline, flat cel shading, vibrant "
         "colours, front view, full body, centered, single character, isolated on a plain pure white background, "
         "no text, no shadow")
BG_STYLE = ("casual mobile game background, soft painterly cel shading, no text, no characters, calm centre")


@dataclass
class Item:
    name: str
    prompt: str
    width: int = 768
    height: int = 768


ITEMS: list[Item] = []


def add(name, prompt, style=STYLE, **kw):
    ITEMS.append(Item(name, f"{style}, {prompt}", **kw))


# dragons: one per merge level, same wording, only colour and grandeur change
DRAGONS = [
    ("dragon1", "a tiny green baby dragon hatchling with small stubby wings and one small horn"),
    ("dragon2", "a small blue frost dragon with icy blue scales and small wings"),
    ("dragon3", "a purple storm dragon with two horns, a head crest and medium wings"),
    ("dragon4", "a red ember dragon with two horns, a spiky crest and large wings"),
    ("dragon5", "a golden sun dragon with a little crown, a glowing aura and big wings"),
    ("dragon6", "a huge dark inferno dragon with a glowing orange belly, three horns, a flaming crest and two large symmetrical bat wings, fully inside the picture"),
]
for n, d in DRAGONS:
    add(n, d, width=768, height=896)

for n, d in [
    ("goblin", "a small green goblin with big pointy ears holding a tiny club"),
    ("imp", "a small red flying imp with little bat wings and a pitchfork tail"),
    ("orc", "a big muscular grey-green orc with tusks and a wooden shield"),
    ("demon", "a large purple horned demon with glowing yellow eyes"),
]:
    add(n, d, width=768, height=896)

add("menu_bg", "a fantasy dragon island at sunset, floating castle, glowing sky, empty foreground", BG_STYLE,
    width=640, height=1136)
add("field", "a top-down grassy battlefield with a dirt road, stone wall at the top, seen from above", BG_STYLE,
    width=640, height=1136)
