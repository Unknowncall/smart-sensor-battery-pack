#!/bin/sh
# Build the board, auto-route it with Freerouting, refill zones, run DRC.
# Output: soil_sensor.kicad_pcb (routed) and build/drc.json.
set -eu
HERE="$(cd "$(dirname "$0")/.." && pwd)"
KPY="$HERE/tools/kpy"
KCLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
JAVA=/opt/homebrew/opt/openjdk/bin/java
FR="$HERE/tools/bin/freerouting-2.5.0.jar"
BOARD="$HERE/soil_sensor.kicad_pcb"
B="$HERE/build"
mkdir -p "$B"

# Route a copy without pours so Freerouting wires GND as an ordinary net
# (with pours present it treats GND as a plane and leaves pads to islands).
"$KPY" "$HERE/gen/build_board.py" "$B/route_input.kicad_pcb" --no-zones 2>/dev/null
"$KPY" "$HERE/gen/route_io.py" export "$B/route_input.kicad_pcb" "$B/soil_sensor.dsn" 2>/dev/null
"$KPY" "$HERE/gen/build_board.py" "$BOARD" 2>/dev/null
"$JAVA" -jar "$FR" -de "$B/soil_sensor.dsn" -do "$B/soil_sensor.ses" -mp "${PASSES:-100}" \
  --gui.enabled=false >"$B/freerouting.log" 2>&1
"$KPY" "$HERE/gen/route_io.py" import "$BOARD" "$B/soil_sensor.ses" 2>/dev/null
"$KCLI" pcb drc --refill-zones --save-board -o /dev/null "$BOARD" >/dev/null 2>&1 || true
"$KPY" "$HERE/gen/route_io.py" stitch "$BOARD" 139 5.6 2>/dev/null | tee "$B/stitch.log"
"$KCLI" pcb drc --refill-zones --save-board --format json --severity-error \
  -o "$B/drc.json" "$BOARD" >/dev/null 2>&1 || true
python3 -I - "$B/drc.json" <<'EOF'
import json, sys, collections
d = json.load(open(sys.argv[1]))
c = collections.Counter(v["type"] for v in d["violations"])
print("violations:", dict(c) or "none", "| unconnected:", len(d.get("unconnected_items", [])))
EOF
