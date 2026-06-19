from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from UnityPy.files.BundleFile import BundleFile
from UnityPy.streams import EndianBinaryReader


DEFAULT_APK = Path(
    r"F:\GameAssistData\app"
    r"\7AD1C3736F7CF7FD2E77C77CCECB6744_840_com.tencent.tmgp.cf_840.apk"
)

# UIResource bundles known to contain ZiZouQi card art, HUD card layers, and icons.
DEFAULT_UA_IDS = (248, 249, 257, 260, 270, 283, 300, 335, 355)


def extract_inner_cabs(apk: Path, out_dir: Path, ua_ids: tuple[int, ...]) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with zipfile.ZipFile(apk) as zf:
        names = set(zf.namelist())
        for ua_id in ua_ids:
            entry = f"assets/Assets/UIResource/ua_{ua_id}.unity3d"
            if entry not in names:
                print(f"[miss] {entry}")
                continue
            raw = zf.read(entry)
            try:
                bundle = BundleFile(EndianBinaryReader(raw), None, name=Path(entry).name)
            except Exception as exc:
                print(f"[fail] {entry}: {type(exc).__name__}: {exc}")
                continue

            for cab_name, reader in bundle.files.items():
                reader.Position = 0
                data = reader.read_bytes(reader.Length)
                out_path = out_dir / f"ua_{ua_id}__{cab_name}"
                out_path.write_bytes(data)
                written.append(out_path)
                print(f"[ok] {entry} -> {out_path} ({len(data)} bytes)")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract known ZiZouQi UIResource UnityFS bundles into inner CAB files.")
    parser.add_argument("--apk", type=Path, default=DEFAULT_APK)
    parser.add_argument("--out", type=Path, default=Path("autochess_dump/icon_zizouqi_cabs"))
    parser.add_argument("--ua", type=int, nargs="*", default=list(DEFAULT_UA_IDS), help="ua_NNN ids to extract")
    args = parser.parse_args()

    written = extract_inner_cabs(args.apk, args.out, tuple(args.ua))
    print(f"written={len(written)}")


if __name__ == "__main__":
    main()
