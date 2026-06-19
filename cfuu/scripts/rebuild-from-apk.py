from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


WEB_DIR = Path(__file__).resolve().parents[1]
ROOT = WEB_DIR.parent
DUMP_DIR = ROOT / "autochess_dump"


PYTHON_STEPS_AFTER_APK = [
    ("crop sprites", ["crop_zizouqi_sprites.py"]),
    ("slice card UI", ["extract_ua257_texture10_slices.py"]),
    ("build image index", ["build_zizouqi_card_image_index.py"]),
    ("organize roles", ["organize_zizouqi_roles.py"]),
    ("organize weapons", ["organize_zizouqi_weapons.py"]),
    ("organize throwables", ["organize_zizouqi_throwables.py"]),
    ("organize items", ["organize_zizouqi_items.py"]),
    ("organize consumes and buffs", ["organize_zizouqi_consume_buffs.py"]),
    ("organize fetters", ["organize_zizouqi_fetters.py"]),
    ("organize maps", ["organize_zizouqi_maps.py"]),
    ("serialize roles before previews", ["serialize_zizouqi_role_data.py"]),
    ("build role previews", ["build_zizouqi_role_card_previews.py"]),
    ("build weapon previews", ["build_zizouqi_weapon_card_previews.py"]),
    ("build throwable previews", ["build_zizouqi_throwable_card_previews.py"]),
    ("build item previews", ["build_zizouqi_item_card_previews.py"]),
    ("build consume previews", ["build_zizouqi_consume_card_previews.py"]),
    ("serialize roles with previews", ["serialize_zizouqi_role_data.py"]),
    ("serialize weapons", ["serialize_zizouqi_weapon_data.py"]),
    ("serialize item-like cards", ["serialize_zizouqi_item_like_data.py"]),
    ("serialize factions", ["serialize_zizouqi_faction_data.py"]),
]


def run(label: str, command: list[str], cwd: Path = ROOT) -> None:
    print(f"\n==> {label}", flush=True)
    print(" ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def remove_tree(path: Path) -> None:
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT):
        raise RuntimeError(f"Refusing to remove path outside workspace: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)


def apk_steps(apk: Path, scan: bool) -> None:
    parse_cmd = [
        sys.executable,
        "parse_autochess_unity.py",
        "--apk",
        str(apk),
        "--out",
        str(DUMP_DIR),
    ]
    if scan:
        parse_cmd.append("--scan")
    run("extract AutoChess tables", parse_cmd)

    run(
        "extract ZiZouQi CAB bundles",
        [
            sys.executable,
            "prepare_zizouqi_cabs.py",
            "--apk",
            str(apk),
            "--out",
            str(DUMP_DIR / "icon_zizouqi_cabs"),
        ],
    )

    cab_files = sorted((DUMP_DIR / "icon_zizouqi_cabs").glob("ua_*__CAB-*"))
    if not cab_files:
        raise RuntimeError(f"No inner CAB files found in {DUMP_DIR / 'icon_zizouqi_cabs'}")

    run(
        "extract CAB textures",
        [
            sys.executable,
            "extract_cf_cab_textures.py",
            *[str(path) for path in cab_files],
            "--out",
            str(DUMP_DIR / "cab_texture_extract"),
        ],
    )


def data_steps() -> None:
    for label, script in PYTHON_STEPS_AFTER_APK:
        run(label, [sys.executable, *script])


def web_steps(skip_build: bool) -> None:
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    run("prepare web data", [npm, "run", "prepare:data"], cwd=WEB_DIR)
    if not skip_build:
        run("build web app", [npm, "run", "build"], cwd=WEB_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild the CFM ZiZouQi data pipeline from APK assets to the cfuu web app.",
    )
    parser.add_argument("--apk", type=Path, help="Path to the new CF Mobile APK.")
    parser.add_argument("--scan", action="store_true", help="Also scan APK assets/bin/Data entries for AutoChess hints.")
    parser.add_argument("--clean", action="store_true", help="Remove generated dump and web public assets/data before running.")
    parser.add_argument("--from-existing-dump", action="store_true", help="Skip APK/CAB extraction and rebuild from current autochess_dump.")
    parser.add_argument("--skip-build", action="store_true", help="Run prepare:data but skip the Vite production build.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apk = args.apk.resolve() if args.apk else None

    if not args.from_existing_dump:
        if apk is None:
            print("--apk is required unless --from-existing-dump is used.", file=sys.stderr)
            return 2
        if not apk.exists():
            print(f"APK not found: {apk}", file=sys.stderr)
            return 2
    elif args.clean:
        print("--clean cannot be combined with --from-existing-dump because it would remove autochess_dump.", file=sys.stderr)
        return 2

    if args.clean:
        remove_tree(DUMP_DIR)
        remove_tree(WEB_DIR / "public" / "assets" / "cards")
        for generated in (
            "cards.json",
            "factions-normalized.json",
            "maps-normalized.json",
            "summary.json",
            "word-explanations.json",
            "roles.json",
            "weapons.json",
            "throwables.json",
            "items.json",
            "consumes.json",
            "buffs.json",
            "factions.json",
            "fetters.json",
            "maps.json",
        ):
            path = WEB_DIR / "public" / "data" / generated
            if path.exists():
                path.unlink()

    if not args.from_existing_dump:
        assert apk is not None
        apk_steps(apk, args.scan)

    data_steps()
    web_steps(args.skip_build)
    print("\nPipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
