from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path("autochess_dump/zizouqi_sprite_crops")
HUD = ROOT / "4U_Hud_ZiZouQi_10"


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def fit_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    src_w, src_h = image.size
    dst_w, dst_h = size
    scale = max(dst_w / src_w, dst_h / src_h)
    resized = image.resize((round(src_w * scale), round(src_h * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - dst_w) // 2
    top = (resized.height - dst_h) // 2
    return resized.crop((left, top, left + dst_w, top + dst_h))


def paste_layer(canvas: Image.Image, layer: Image.Image, xy: tuple[int, int], size: tuple[int, int] | None = None) -> None:
    if size is not None:
        layer = layer.resize(size, Image.Resampling.LANCZOS)
    canvas.alpha_composite(layer, xy)


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\arialbd.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def shield_badge(size: tuple[int, int], fill: tuple[int, int, int, int], outline: tuple[int, int, int, int]) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pts = [(w // 2, 0), (w - 1, h // 4), (w - 5, h - 5), (w // 2, h - 1), (4, h - 5), (0, h // 4)]
    d.polygon(pts, fill=fill, outline=outline)
    return im


def draw_stat(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fill: tuple[int, int, int], stroke: tuple[int, int, int]) -> None:
    draw.text(xy, text, font=font(44), fill=fill, stroke_width=2, stroke_fill=stroke)


def compose_dao_feng() -> Path:
    out_dir = Path("autochess_dump/composed_card_previews")
    out_dir.mkdir(parents=True, exist_ok=True)

    card_w, card_h = 168, 224
    canvas = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))

    bg = load_rgba(HUD / "4U_Hud_ZiZouQi_Card_Bg_01.png")
    main = load_rgba(HUD / "4U_Hud_ZiZouQi_Card_Mian_JInSe.png")
    bottom = load_rgba(HUD / "4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_JinSe.png")
    role = load_rgba(ROOT / "Icon_Pvp_ZiZouQi_Role_01" / "Icon_ZiZouQi_JueSe_DaoFeng_BWZ.png")

    paste_layer(canvas, fit_cover(bg, (card_w - 8, card_h - 8)), (4, 4))
    paste_layer(canvas, main, (17, 10), (134, 183))
    paste_layer(canvas, bottom, (10, 9), (148, 206))
    paste_layer(canvas, role, (1, -1), (168, 224))

    d = ImageDraw.Draw(canvas)

    # Approximate the in-game stat emblems; the extracted stat sprites are
    # currently transparent, so these placeholders keep the preview readable.
    canvas.alpha_composite(shield_badge((34, 46), (170, 48, 52, 230), (83, 28, 35, 255)), (4, 111))
    canvas.alpha_composite(shield_badge((34, 46), (37, 155, 111, 230), (20, 83, 67, 255)), (131, 111))
    draw_stat(d, (8, 106), "8", (247, 98, 108), (82, 30, 39))
    draw_stat(d, (111, 106), "13", (82, 216, 157), (22, 82, 67))

    # Card outline and name plate, approximating the runtime UI composition.
    d.rounded_rectangle((3, 3, 165, 221), radius=5, outline=(174, 194, 215, 255), width=3)
    d.rounded_rectangle((6, 6, 162, 218), radius=4, outline=(37, 57, 74, 230), width=2)
    d.rectangle((21, 184, 147, 222), fill=(34, 51, 66, 235))
    name_font = font(24)
    bbox = d.textbbox((0, 0), "刀锋", font=name_font)
    d.text(((card_w - (bbox[2] - bbox[0])) // 2, 190), "刀锋", font=name_font, fill=(191, 210, 224))

    out = out_dir / "DaoFeng_gold_preview.png"
    canvas.save(out)
    return out


def compose_dao_feng_variants() -> list[Path]:
    out_dir = Path("autochess_dump/composed_card_previews")
    out_dir.mkdir(parents=True, exist_ok=True)

    bg = load_rgba(HUD / "4U_Hud_ZiZouQi_Card_Bg_01.png")
    main = load_rgba(HUD / "4U_Hud_ZiZouQi_Card_Mian_JInSe.png")
    frame = load_rgba(HUD / "4U_Hud_ZiZouQi_Card_ShopAndMainBottom_WeaponAndRole_JinSe.png")
    role = load_rgba(ROOT / "Icon_Pvp_ZiZouQi_Role_01" / "Icon_ZiZouQi_JueSe_DaoFeng_BWZ.png")
    paths = []

    configs = [
        {
            "name": "DaoFeng_gold_variant_a_frame_native.png",
            "size": (148, 206),
            "bg": ((0, 0), (148, 203)),
            "main": ((10, 0), (129, 176)),
            "role": ((-18, -18), (178, 237)),
            "frame": ((0, 0), (148, 206)),
            "namebar": (19, 166, 129, 203),
            "atk": ((-5, 102), (2, 96)),
            "hp": ((113, 102), (104, 96)),
        },
        {
            "name": "DaoFeng_gold_variant_b_target_ratio.png",
            "size": (165, 218),
            "bg": ((6, 5), (153, 211)),
            "main": ((18, 6), (142, 188)),
            "role": ((-8, -16), (176, 235)),
            "frame": ((5, 4), (155, 216)),
            "namebar": (28, 178, 137, 215),
            "atk": ((-3, 112), (3, 106)),
            "hp": ((128, 112), (116, 106)),
        },
        {
            "name": "DaoFeng_gold_variant_c_tighter_crop.png",
            "size": (165, 218),
            "bg": ((6, 5), (153, 211)),
            "main": ((18, 6), (142, 188)),
            "role": ((-18, -18), (185, 246)),
            "frame": ((5, 4), (155, 216)),
            "namebar": (28, 178, 137, 215),
            "atk": ((-3, 112), (3, 106)),
            "hp": ((128, 112), (116, 106)),
        },
        {
            "name": "DaoFeng_gold_variant_d_clean_frame.png",
            "size": (165, 218),
            "bg": ((6, 5), (153, 211)),
            "main": ((18, 6), (142, 188)),
            "role": ((-8, -16), (176, 235)),
            "frame": None,
            "namebar": (17, 175, 148, 215),
            "atk": ((-3, 112), (3, 106)),
            "hp": ((128, 112), (116, 106)),
        },
    ]

    for cfg in configs:
        canvas = Image.new("RGBA", cfg["size"], (0, 0, 0, 0))
        paste_layer(canvas, fit_cover(bg, cfg["bg"][1]), cfg["bg"][0])
        paste_layer(canvas, main, cfg["main"][0], cfg["main"][1])
        paste_layer(canvas, role, cfg["role"][0], cfg["role"][1])
        if cfg["frame"] is not None:
            paste_layer(canvas, frame, cfg["frame"][0], cfg["frame"][1])
        d = ImageDraw.Draw(canvas)
        if cfg["frame"] is None:
            d.rounded_rectangle((2, 2, cfg["size"][0] - 3, cfg["size"][1] - 3), radius=5, outline=(178, 199, 220, 255), width=3)
            d.rounded_rectangle((7, 7, cfg["size"][0] - 8, cfg["size"][1] - 8), radius=4, outline=(34, 56, 73, 235), width=2)
        x1, y1, x2, y2 = cfg["namebar"]
        d.rectangle((x1, y1, x2, y2), fill=(34, 51, 66, 238))
        canvas.alpha_composite(shield_badge((34, 46), (170, 48, 52, 235), (83, 28, 35, 255)), cfg["atk"][0])
        canvas.alpha_composite(shield_badge((34, 46), (37, 155, 111, 235), (20, 83, 67, 255)), cfg["hp"][0])
        draw_stat(d, cfg["atk"][1], "8", (247, 98, 108), (82, 30, 39))
        draw_stat(d, cfg["hp"][1], "13", (82, 216, 157), (22, 82, 67))
        name_font = font(24)
        bbox = d.textbbox((0, 0), "刀锋", font=name_font)
        d.text(((cfg["size"][0] - (bbox[2] - bbox[0])) // 2, y1 + 6), "刀锋", font=name_font, fill=(191, 210, 224))
        out = out_dir / cfg["name"]
        canvas.save(out)
        paths.append(out)
    return paths


if __name__ == "__main__":
    print(compose_dao_feng())
    for path in compose_dao_feng_variants():
        print(path)
