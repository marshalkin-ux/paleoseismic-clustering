"""Regenerate only viz5 and viz6 from generate_visualizations.py."""
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

spec = importlib.util.spec_from_file_location(
    "gen_viz", ROOT / "scripts" / "generate_visualizations.py"
)

# We execute the module source manually so that the module-level
# VIZ_FUNCS loop doesn't run all 6 visualizations.
# Instead, we exec only the function definitions, then call viz5 + viz6.

source = (ROOT / "scripts" / "generate_visualizations.py").read_text(encoding="utf-8")

# Strip the module-level execution block (everything after "VIZ_FUNCS = [")
cutoff = source.find("\nVIZ_FUNCS = [")
if cutoff == -1:
    cutoff = source.find("\nfor fn in VIZ_FUNCS")
if cutoff == -1:
    cutoff = len(source)

module_code = source[:cutoff]

gen_viz_path = str(ROOT / "scripts" / "generate_visualizations.py")
ns: dict = {"__file__": gen_viz_path, "__name__": "__main__"}
exec(compile(module_code, gen_viz_path, "exec"), ns)

import traceback

for name, fn in [("viz5_heatmap_regions", ns["viz5_heatmap_regions"]),
                 ("viz6_series_s170", ns["viz6_series_s170"])]:
    try:
        fn()
    except Exception as e:
        print(f"\n  ✗ {name} FAILED: {e}")
        traceback.print_exc()

print("\nFile sizes:")
FIGURES = ROOT / "figures"
for f in sorted(FIGURES.glob("viz5*.png")) + sorted(FIGURES.glob("viz6*.png")):
    print(f"  {f.name}: {f.stat().st_size / 1024:.0f} KB  (mtime: {f.stat().st_mtime:.0f})")
