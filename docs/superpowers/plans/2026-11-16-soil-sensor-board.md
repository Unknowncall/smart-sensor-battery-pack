# All-in-One Soil Sensor Board Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A JLC-assembled 2-layer board (ESP32-C6, 18650 holder + charging + protection, capacitive soil probe, SHTC3) with Gerbers/BOM/CPL ready to order and an ESPHome config ready to flash.

**Architecture:** One Python netlist module is the single source of truth for parts and connections. A pcbnew-API script builds the `.kicad_pcb` from it (footprints, outline, placement, probe electrode, keep-outs); Freerouting routes it; kicad-cli runs DRC and exports JLC files. No schematic sheet in v1: a generated netlist report stands in for review, and a connectivity test stands in for ERC.

**Tech Stack:** KiCad 10.0.8 (bundled Python 3.9 `pcbnew`), kicad-cli, easyeda2kicad (via `uvx`) for footprints KiCad lacks, Freerouting (JDK 21), pytest (KiCad's Python), ESPHome (via `uvx`).

**Spec:** `docs/superpowers/specs/2026-11-16-soil-probe-board-design.md`

## Global Constraints

- All parts top side; JLC Economic PCBA; LeadFree HASL; black mask; 2 layers, 1.6 mm.
- Board about 25 mm x 155 mm: head ~85 mm (above soil), probe ~70 mm (in soil), pointed tip.
- Extended-fee parts limited to exactly: ESP32-C6-MINI-1-N4 C5736265, XC6220B331MR C3040644, TYPE-C-31-M-12 C165948, SHTC3 C194656, BH-18650-B1BA002 C2988620, XB5353A C80628. Every other part must be JLC Basic or Preferred (verify each LCSC code).
- TP4056 C16581 (Preferred). 1N4148WS C2128 (Basic). AO3401A C15127 (Basic).
- No exposed copper and no vias below the probe fill line.
- ESP32-C6-MINI-1 antenna at the board's top edge; no copper on either layer inside the module's antenna keep-out.
- JLC design rules: track/clearance >= 0.15 mm, via 0.3 mm drill / 0.6 mm pad, board-edge clearance >= 0.3 mm.
- Tools run with KiCad's Python: `KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9`, `KCLI=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`.

## Fixed circuit decisions (implementer does not choose these)

| Net / function | Decision |
|---|---|
| ESP32 GPIO | PWM probe drive IO19; soil ADC IO2; battery ADC IO3; I2C SDA IO22, SCL IO23; USB D- IO12, D+ IO13; IO9 to test pad TP_BOOT (with GND test pad beside it); EN 10k pull-up + 1 uF to GND |
| USB-C | VBUS, GND, CC1/CC2 each 5.1k to GND, D+/D- (both A/B pins tied) to IO13/IO12; shield to GND |
| Charger | TP4056: VCC=VBUS (10 uF in), BAT to cell+ node (10 uF), RPROG 2.4k (~500 mA), CHRG through 1k to red 0603 LED (C2286) to VBUS, STDBY unconnected, TEMP to GND, CE to VCC |
| Protection | XB5353A between cell- and system GND per its datasheet application circuit (the chip includes the MOSFETs) |
| Reverse cell | AO3401A P-FET in the cell+ path as ideal-diode reverse protection (gate to GND via 100k) |
| Regulator | XC6220B331MR from protected cell+ (VBAT), 1 uF in, 1 uF out, plus 22 uF bulk on 3V3 near the module, plus 10 uF + 100 nF at the module |
| Battery sense | VBAT -> 1M -> IO3 -> 1M -> GND, 100 nF on IO3 |
| Soil probe | IO19 -> 1k -> electrode node; electrode node -> 1N4148WS anode; cathode -> 100 nF to GND and 1M to GND -> IO2. Values from b-parasite's published circuit if its licence allows; otherwise keep these |
| SHTC3 | 3V3, GND, SDA/SCL; 10k pull-ups to 3V3 on SDA and SCL; 100 nF decoupling |

## Review Focus

1. **USB plugged in, no cell:** board must still power up and flash (TP4056 output alone feeds the regulator). Pin: netlist test asserts VBAT reaches U_LDO input through the charger output path with no cell present (TP4056 BAT and VBAT share a node).
2. **Cell inserted backwards:** nothing may be damaged. Pin: netlist test asserts the AO3401A sits between holder + and VBAT with the documented orientation.
3. **WiFi TX burst on a sagging cell:** brown-out resets. Pin: netlist test asserts >= 22 uF on 3V3.
4. **Antenna next to the ground pour:** WiFi range collapses. Pin: placement test asserts no copper zone or track intersects the module keep-out rectangle on F.Cu or B.Cu.
5. **Probe pushed in past the fill line:** soil touching vias or pads. Pin: placement test asserts zero vias and zero non-electrode pads below the fill line y-coordinate.

---

### Task 1: Tooling and footprints for parts KiCad lacks

**Files:**
- Create: `hardware/soil-sensor/lib/soil_sensor.pretty/` (footprints), `hardware/soil-sensor/lib/soil_sensor.kicad_sym`, `hardware/soil-sensor/lib/3d/`
- Create: `hardware/soil-sensor/tools/fetch_parts.sh`
- Test: `hardware/soil-sensor/tests/test_footprints.py`

**Interfaces:**
- Produces: footprint names `soil_sensor:BH-18650-B1BA002`, `soil_sensor:XB5353A_SOT-23-5`, `soil_sensor:TP4056_ESOP-8`, `soil_sensor:XC6220_SOT-23-5`, `soil_sensor:SHTC3_DFN-4`; stock `RF_Module:ESP32-C6-MINI-1`, `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`, `Package_TO_SOT_SMD:SOT-23`, `Resistor_SMD:R_0402_1005Metric`, `Capacitor_SMD:C_0402_1005Metric`, `Capacitor_SMD:C_0805_2012Metric`, `LED_SMD:LED_0603_1608Metric`, `Diode_SMD:D_SOD-323`.

- [ ] **Step 1:** Write `test_footprints.py`: loads each footprint above with `pcbnew.FootprintLoad` and asserts pad counts: BH-18650 2 electrical pads, XB5353A 5, TP4056 9 (8 + EP), XC6220 5, SHTC3 5 (4 + EP), ESP32-C6-MINI-1 matches KiCad stock count, TYPE-C-31-M-12 includes A5/B5 (CC) and A6/A7/B6/B7.
- [ ] **Step 2:** Run `$KPY -m pytest hardware/soil-sensor/tests/test_footprints.py -v` — expect FAIL (library missing).
- [ ] **Step 3:** `fetch_parts.sh` runs `uvx easyeda2kicad --full --lcsc_id <id> --output hardware/soil-sensor/lib/soil_sensor` for C2988620, C80628, C16581, C3040644, C194656, then renames footprints to the names above. Install JDK 21 (`brew install openjdk@21`) and download the Freerouting release jar into `hardware/soil-sensor/tools/` (pin the version in the script). Compare the holder footprint's pad pitch against the C2988620 datasheet drawing.
- [ ] **Step 4:** Re-run the test — expect PASS.
- [ ] **Step 5:** Commit.

### Task 2: Netlist module and connectivity tests

**Files:**
- Create: `hardware/soil-sensor/gen/parts.py`, `hardware/soil-sensor/gen/netlist.py`
- Test: `hardware/soil-sensor/tests/test_netlist.py`

**Interfaces:**
- Produces: `parts.PARTS: dict[str, Part]` with `Part(ref, value, footprint, lcsc, tier)`; `netlist.NETS: dict[str, list[tuple[str, str]]]` mapping net name to `(ref, pad)` pairs; `netlist.report() -> str` (markdown netlist for review).

- [ ] **Step 1:** Write tests: every pad of every part appears in exactly one net or in `netlist.NO_CONNECT`; no net has fewer than 2 pads; every `Part.tier` is one of `basic|preferred|extended` and the set of `extended` LCSC codes equals the six in Global Constraints; the five Review Focus nets/parts assertions (items 1–3) hold; net names `VBUS, VBAT, VCELL_P, VCELL_N, 3V3, GND, SDA, SCL, USB_DP, USB_DN, PROBE_DRV, PROBE_EL, SOIL_ADC, BAT_ADC, EN, BOOT`.
- [ ] **Step 2:** Run tests — expect FAIL.
- [ ] **Step 3:** Implement `parts.py` and `netlist.py` from the "Fixed circuit decisions" table and each part's datasheet pin map (cite the datasheet page in a comment per part).
- [ ] **Step 4:** Run tests — expect PASS. Write `hardware/soil-sensor/NETLIST.md` from `report()`.
- [ ] **Step 5:** Commit.

### Task 3: Board build script (outline, placement, probe, keep-outs)

**Files:**
- Create: `hardware/soil-sensor/gen/build_board.py`, output `hardware/soil-sensor/soil_sensor.kicad_pcb`, `soil_sensor.kicad_pro`
- Test: `hardware/soil-sensor/tests/test_placement.py`

**Interfaces:**
- Consumes: `PARTS`, `NETS` from Task 2.
- Produces: `build_board.build(path: str) -> None`; constants `FILL_LINE_Y_MM`, `KEEPOUT_RECT_MM`.

- [ ] **Step 1:** Write `test_placement.py`: board outline is closed, 25 x 155 mm +/- 2 mm; all footprints on F.Cu; footprints don't overlap courtyards; USB-C at the top edge, ESP32 antenna within 0.5 mm of the top edge; every pad has the net `NETS` assigns; Review Focus 4 and 5 assertions; probe electrode copper exists only on F.Cu below `FILL_LINE_Y_MM`, B.Cu below it is a GND zone; SHTC3 sits on a peninsula with a >= 1 mm slot between it and the rest of the head.
- [ ] **Step 2:** Run — expect FAIL.
- [ ] **Step 3:** Implement `build()` with the pcbnew API: Edge.Cuts outline with pointed tip and SHTC3 slot; placement top-to-bottom: USB-C + ESP32 (antenna up), holder, power parts beside/under holder ends, SHTC3 peninsula, fill line silkscreen, probe electrode (solid F.Cu shape ~10 mm wide over most of the probe length, connected to the diode by a track above the fill line); module keep-out rule area on both layers; GND zones on both layers (excluded under the keep-out and from F.Cu below the fill line except the electrode); JLC rules in the board design settings; silkscreen title, polarity marks at the holder, "LCSC JLCJLCJLCJLC" order-number placeholder.
- [ ] **Step 4:** Run — expect PASS.
- [ ] **Step 5:** Commit.

### Task 4: Routing and DRC

**Files:**
- Create: `hardware/soil-sensor/tools/route.sh`
- Modify: `hardware/soil-sensor/soil_sensor.kicad_pcb`

**Interfaces:**
- Consumes: board from Task 3.

- [ ] **Step 1:** `route.sh`: export DSN via `pcbnew.ExportSpecctraDSN`, run Freerouting headless (`java -jar freerouting.jar -de in.dsn -do out.ses -mp 50`), import SES via `pcbnew.ImportSpecctraSES`, refill zones, save.
- [ ] **Step 2:** Run `$KCLI pcb drc --exit-code-violations --severity-error --schematic-parity=false -o drc.rpt soil_sensor.kicad_pcb` — expect exit 0 and "0 unconnected items".
- [ ] **Step 3:** Re-run `test_placement.py` on the routed board — expect PASS (catches routes added into the keep-out or vias below the fill line). Fix by keep-out rule areas, not by deleting tests.
- [ ] **Step 4:** Commit.

### Task 5: JLC outputs and renders

**Files:**
- Create: `hardware/soil-sensor/tools/export_jlc.py`, outputs in `hardware/soil-sensor/jlcpcb/` (gerbers, drills, `BOM-JLCPCB.csv`, `CPL-JLCPCB.csv`), `hardware/soil-sensor/renders/top.png`, `bottom.png`
- Test: `hardware/soil-sensor/tests/test_jlc_outputs.py`

- [ ] **Step 1:** Test: BOM rows group identical (value, footprint, LCSC); every placed ref is in BOM and CPL; CPL layer is `Top` for all; LCSC codes match `PARTS`; gerber set contains F/B Cu, Mask, Paste, Silk, Edge_Cuts and PTH/NPTH drills.
- [ ] **Step 2:** Run — FAIL. Implement `export_jlc.py` with kicad-cli (gerbers with `--no-protel-ext --subtract-soldermask`, drill excellon, `pcb export pos`) and the same BOM/CPL conversion used in `jlcpcb/` for the old board. Render with `$KCLI pcb render --side top/bottom`.
- [ ] **Step 3:** Run — PASS. Commit.

### Task 6: ESPHome firmware config

**Files:**
- Create: `hardware/soil-sensor/firmware/soil-sensor.yaml`, `firmware/secrets.example.yaml`

- [ ] **Step 1:** YAML: `esp32` board `esp32-c6-devkitc-1`, ESP-IDF framework; `output: ledc` on GPIO19 at the highest frequency ESPHome's LEDC accepts on the C6; `adc` on GPIO2 (soil, raw volts) and GPIO3 (battery, multiply 2.0); template sensor for moisture % using `calibrate_linear` from two placeholders `soil_dry_v`, `soil_wet_v`; `shtc3` on SDA 22 / SCL 23; `deep_sleep` run 20 s, sleep 10 min; on boot: turn LEDC on, wait 200 ms, update soil, turn off.
- [ ] **Step 2:** Run `uvx esphome config hardware/soil-sensor/firmware/soil-sensor.yaml` with `secrets.example.yaml` copied to `secrets.yaml` — expect valid config. Then `uvx esphome compile` — expect success.
- [ ] **Step 3:** Commit.

### Task 7: Review package and shopping list

- [ ] **Step 1:** Upload board + firmware to the fork; update root README with a section linking `hardware/soil-sensor/` (renders, NETLIST.md, JLC files, firmware).
- [ ] **Step 2:** Run the JLC quote with the new files (Economic, top, 2 assembled, black, LeadFree HASL) and record the exact total; confirm the Extended fee count equals 6.
- [ ] **Step 3:** Shopping list: JLC order (from Step 2); anything else needed (none expected: owner has 18650 cells and a USB-C cable). Commit.

## Not covered (needs hardware)
Real-behavior proof (power-up, flashing, probe readings, battery life) can only happen once boards arrive. Every step above is verified in software only.
