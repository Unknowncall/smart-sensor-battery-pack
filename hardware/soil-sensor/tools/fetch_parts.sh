#!/bin/sh
# Fetch footprints/symbols/3D models for the LCSC parts KiCad's stock libraries
# don't have, then give each footprint the stable name the netlist uses.
set -eu
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/lib/soil_sensor"
mkdir -p "$HERE/lib"

fetch() { # lcsc_id target_name
  before=$(ls "$OUT.pretty" 2>/dev/null || true)
  uvx --python 3.12 --from easyeda2kicad==1.0.1 easyeda2kicad --full --lcsc_id "$1" --output "$OUT" --overwrite >/dev/null
  new=$(ls "$OUT.pretty" | grep -vxF "$before" | grep -v "^$2.kicad_mod$" | head -1 || true)
  if [ -n "$new" ]; then
    mv "$OUT.pretty/$new" "$OUT.pretty/$2.kicad_mod"
    sed -i '' "1s/(footprint \"[^\"]*\"/(footprint \"$2\"/" "$OUT.pretty/$2.kicad_mod"
  fi
  echo "$1 -> $2"
}

fetch C2988620 BH-18650-B1BA002
fetch C80628   XB5353A_SOT-23-5
fetch C16581   TP4056_ESOP-8
fetch C3040644 XC6220_SOT-23-5
fetch C194656  SHTC3_DFN-4

# Auto-router. Freerouting 2.5.0 needs Java 25+ (brew install openjdk).
FR="$HERE/tools/bin/freerouting-2.5.0.jar"
if [ ! -f "$FR" ]; then
  mkdir -p "$HERE/tools/bin"
  curl -sL -o "$FR" https://github.com/freerouting/freerouting/releases/download/v2.5.0/freerouting-2.5.0.jar
fi
echo "f6f51bb02245e8e717f9359bd260cc9c5c0b1bc0acc8b7cb2cd5b8ffeb5de3c7  $FR" | shasum -a 256 -c -

# EasyEDA exports the holder's locating peg as a plated hole with no ring; it is non-plated.
sed -i '' 's/(pad "" thru_hole circle (at 8.00 -35.84)/(pad "" np_thru_hole circle (at 8.00 -35.84)/' "$OUT.pretty/BH-18650-B1BA002.kicad_mod"
