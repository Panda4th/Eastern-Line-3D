"""
Rebuild eastern-front-3d.html with the review fixes, without running assemble.py
(fontTools is not available in this environment, and the output/ dir does not exist).

Strategy: instead of re-deriving assemble.py's placeholder substitution, this script
performs whole-block literal replacements against the ALREADY ASSEMBLED production
HTML. Each old block below is verified byte-identical (occurs exactly once) before
being swapped for the corresponding new block from the edited source files:
  - assets/template.html : CSS line (line 3) and the body-markup prefix on line 6
    (everything up to and including the "<script>" that opens THREE_CODE).
  - assets/app.js : the whole file, verbatim (it is embedded byte-for-byte between
    the HISTORY_JSON script tag and the closing </script> in the shipped HTML).
  - land-50m.json -> assets/land-crop.json (T-8), only if the crop file exists AND
    passes verify_land_crop.cjs's geoPath-identity gate (checked by the caller /
    documented in the final report; this script itself does not re-run node).

Never overwrites the original artifact. Output is a new file, eastern-front-3d-v2.html.
NOTE: OUTPUT_PATH must be changed to an unused filename before every re-run; re-running with a
stale OUTPUT_PATH is rejected by the guard in main() below (the file it would overwrite already exists).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_PATH = Path("C:/Users/meiko.nin/.claude/projects/Eastern Front/eastern-front-3d.html")
OUTPUT_PATH = Path("C:/Users/meiko.nin/.claude/projects/Eastern Front/eastern-front-3d-v3.html")

APP_ORIG = ROOT / "assets" / "app.js.orig"
APP_NEW = ROOT / "assets" / "app.js"
TPL_ORIG = ROOT / "assets" / "template.html.orig"
TPL_NEW = ROOT / "assets" / "template.html"
LAND_ORIG = ROOT / "land-50m.json"
LAND_CROP = ROOT / "assets" / "land-crop.json"

# Set to False to skip T-8 (land crop) even if land-crop.json exists.
APPLY_T8_LAND_CROP = True


def read_bytes(p: Path) -> bytes:
    return p.read_bytes()


def script_prefix(line6: bytes, marker: bytes) -> bytes:
    """Everything in the template's line-6 up to and including the literal
    '<script>' tag that immediately precedes the given placeholder token."""
    idx = line6.index(marker)
    return line6[: idx + len(b"<script>")]


def build_replacements():
    reps = []

    tpl_orig_lines = read_bytes(TPL_ORIG).split(b"\n")
    tpl_new_lines = read_bytes(TPL_NEW).split(b"\n")
    assert len(tpl_orig_lines) == len(tpl_new_lines) == 7, "template.html line count changed unexpectedly"

    old_css, new_css = tpl_orig_lines[2], tpl_new_lines[2]
    reps.append(("template CSS (line 3)", old_css, new_css))

    old_prefix = script_prefix(tpl_orig_lines[5], b"<script>THREE_CODE")
    new_prefix = script_prefix(tpl_new_lines[5], b"<script>THREE_CODE")
    reps.append(("template body markup prefix (line 6)", old_prefix, new_prefix))

    old_app, new_app = read_bytes(APP_ORIG), read_bytes(APP_NEW)
    reps.append(("app.js (whole file)", old_app, new_app))

    if APPLY_T8_LAND_CROP:
        if not LAND_CROP.exists():
            print(f"ABORT: {LAND_CROP} is missing but APPLY_T8_LAND_CROP is True.", file=sys.stderr)
            sys.exit(1)
        old_land, new_land = read_bytes(LAND_ORIG), read_bytes(LAND_CROP)
        reps.append(("LAND topology (T-8 crop)", old_land, new_land))

    return reps


def main():
    if OUTPUT_PATH.resolve() == INPUT_PATH.resolve():
        print("ABORT: OUTPUT_PATH must differ from INPUT_PATH (the input is unrecoverable).", file=sys.stderr)
        sys.exit(1)
    if OUTPUT_PATH.exists():
        print(f"ABORT: {OUTPUT_PATH} already exists. Pick an unused filename.", file=sys.stderr)
        sys.exit(1)

    src = read_bytes(INPUT_PATH)
    orig_len = len(src)
    applied_t8 = False

    for name, old, new in build_replacements():
        count = src.count(old)
        if count != 1:
            print(f"ABORT: '{name}' old-block occurs {count} times (expected 1). No output written.", file=sys.stderr)
            sys.exit(1)
        src = src.replace(old, new, 1)
        if name.startswith("LAND"):
            applied_t8 = True

    out_lines = src.split(b"\n")
    in_lines = read_bytes(INPUT_PATH).split(b"\n")  # re-read original for the line-diff check below
    assert len(out_lines) == len(in_lines), f"line count changed: {len(in_lines)} -> {len(out_lines)}"
    if len(out_lines) != 260:  # 259 newlines -> 260 pieces from split('\n')
        print(f"ABORT: expected 260 split('\\n') pieces (259 lines), got {len(out_lines)}.", file=sys.stderr)
        sys.exit(1)

    # NOTE (review N-6): a per-line byte-length check on lines 2, 12, 14, 16, 18 (and 17
    # when T-8 is not applied) used to live here. It was removed because it was fully
    # subsumed by the allowed-line-set check below: those line numbers are not in
    # `allowed`, so any change to them (length-changing or not) already aborts via the
    # "stray" check. Removing it only changes the abort message, not the exit behavior.

    allowed = {3, 6} | set(range(19, 109))
    if applied_t8:
        allowed.add(17)
    diffed = {i + 1 for i in range(len(in_lines)) if in_lines[i] != out_lines[i]}
    stray = diffed - allowed
    if stray:
        print(f"ABORT: unexpected diff on line(s) {sorted(stray)} outside allowed range.", file=sys.stderr)
        sys.exit(1)

    OUTPUT_PATH.write_bytes(src)
    print("OK: wrote", OUTPUT_PATH)
    print("input bytes", orig_len, "-> output bytes", len(src))
    print("T-8 land crop applied:", applied_t8)
    print("diffed lines:", sorted(diffed))


if __name__ == "__main__":
    main()
