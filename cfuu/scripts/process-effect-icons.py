from pathlib import Path

from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = PROJECT_ROOT.parent / "autochess_dump" / "zizouqi_sprite_crops" / "64_Icon_ZhanDou_1024x1024"
OUTPUT_ROOT = PROJECT_ROOT / "public" / "assets" / "effects"

ICONS = {
    "4U_Hud_CardMode_CardEffect_ChaoFeng.png": "taunt.png",
    "4U_Hud_CardMode_CardEffect_Stop.png": "stop.png",
}


def process_icon(source: Path, target: Path) -> None:
    image = Image.open(source).convert("RGBA")
    red, green, blue, alpha = image.split()
    image = Image.merge("RGBA", (blue, green, red, alpha))
    image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)


for source_name, output_name in ICONS.items():
    process_icon(SOURCE_ROOT / source_name, OUTPUT_ROOT / output_name)

print(f"Processed {len(ICONS)} effect icons.")
