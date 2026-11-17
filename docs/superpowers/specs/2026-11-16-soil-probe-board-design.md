# Soil probe board: design

Date: 2026-11-16
Status: draft for approval

## Why

The owner wants battery soil sensors for their plants, reporting to Home
Assistant, and wants the part that is theirs made in house. Earlier in the
project a full custom battery board (charger, protection, LDO, XIAO sockets)
priced out at about $55 for two assembled boards plus about $65 of other
parts and shipping, which is far too much. The fix is to buy the commodity
part (MCU + LiPo charging) and design only the probe.

## Goals

- A custom PCB that is the soil probe itself: capacitive electrodes on the
  board, plus air temperature and humidity.
- Plugs into a bought MCU board with a cable. No hand soldering anywhere.
- Fully assembled by JLCPCB, Economic PCBA, top side only.
- Works with ESPHome over WiFi, deep-sleeping between readings.
- Cheap enough per unit that a second batch is just the PCB order.

## Non-goals

- On-board battery charging, protection, regulators, or a radio (the MCU
  board does those).
- Zigbee firmware in v1 (possible later on the same hardware).
- Soil EC/fertility, light, or anything beyond moisture + temperature + RH.

## Anti-goals (would make it a failure even if it works)

- Any step that needs the owner to solder.
- A probe that corrodes (bare copper in soil).
- A design that needs custom firmware flashed onto a chip on the probe board.

## Constraints

- JLC: every non-Basic part costs $3.09 per order; keep Extended parts to
  the minimum needed. Setup $8.24 + stencil $1.55 per order.
- Economic PCBA must use a non-OSP finish (HASL or LeadFree HASL).
- MCU board: Adafruit ESP32-C6 Feather (product 5933): ESP32-C6, LiPo
  charging + JST-PH battery jack, MAX17048 fuel gauge, STEMMA QT (JST-SH
  4-pin I2C, 3.3V) port, ~17 uA deep sleep. $14.95, out of stock at Adafruit
  on 2026-11-16, so source from a distributor.
- The only no-solder link to the Feather is STEMMA QT, so the probe must
  speak I2C.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| **A (picked)** | Feather + probe board with TI FDC1004 capacitance-to-digital chip + SHTC3, STEMMA QT cable | No firmware on the probe; FDC1004 is an Extended part (~$4) with limited JLC stock; needs a small ESPHome external component |
| B | Feather + probe board with a tiny MCU (CH32V003 class) doing RC/charge-time sensing over I2C | Cheaper chip, but needs our own probe firmware and a programmer, which breaks "no soldering / no extra tooling" |
| C | FireBeetle 2 ESP32-C6 + analog probe (TLC555-style oscillator) read by ADC | Cheapest ($6.90 board, Basic parts) but the FireBeetle ships with loose headers, so it needs soldering. Rejected by the owner |

The owner picked the Feather / plug-in-only path; A is the way to make the
probe talk I2C without a second firmware.

## Design

### Board
- 2-layer FR-4, 1.6 mm, LeadFree HASL, black or green. About 22 mm wide,
  about 90 mm long, pointed tip for pushing into soil.
- Two zones:
  - **Head (top ~25 mm, stays above soil):** FDC1004, SHTC3, decoupling,
    STEMMA QT (JST-SH 4-pin, right angle) connector at the top edge.
  - **Probe (bottom ~65 mm, goes in soil):** sensing electrode connected to
    FDC1004 CIN1, surrounded by a shield trace driven from SHLD1, with a GND
    reference on the back. Electrodes fully under solder mask; no exposed
    copper, no vias in the soil zone.
- SHTC3 sits on a peninsula cut by a slot so heat and soil moisture
  readings don't skew air temperature/RH.
- Fill line on silkscreen marking the maximum insertion depth.

### Parts (all top side, all placed by JLC)
| Ref | Part | LCSC | JLC tier |
|---|---|---|---|
| U1 | FDC1004QDGSRQ1 (VSSOP-10) | C2652097 | Extended |
| U2 | SHTC3 (DFN-4 2x2) | C194656 | Extended |
| J1 | JST-SH 4-pin right-angle (STEMMA QT) SM04B-SRSS-TB | C160404 | Extended |
| C1-C3 | 100 nF 0402 | C1525 | Basic |
| C4 | 1 uF 0402 (FDC1004 VDD bulk) | Basic part chosen at layout | Basic |

I2C pull-ups: the Feather's STEMMA QT port already has them; add 10k
footprints marked do-not-place as a fallback.

STEMMA QT pinout (Adafruit): GND, 3.3V, SDA, SCL.

I2C addresses: FDC1004 0x50, SHTC3 0x70, MAX17048 (on Feather) 0x36. No
conflicts.

### Firmware (ESPHome, on the Feather)
- `shtc3` sensor (built in).
- MAX17048 battery % via ESPHome's MAX17043-family support if present;
  otherwise a small lambda.
- FDC1004: an ESPHome external component (C++) that sets CAPDAC, triggers a
  single measurement on CIN1, reads the 24-bit result, and reports pF.
  Moisture % is a calibration curve (dry air / water endpoints) done in YAML.
- Deep sleep 10 minutes between readings.

### Power / battery
- 1000 mAh LiPo with JST-PH 2.0 plug. **Polarity must match Adafruit's**
  (many AliExpress LiPos are reversed and will damage the Feather).
- Estimated life on WiFi, every 10 minutes: about 2 months per charge
  (estimate, to be measured). Charges over the Feather's USB-C.

### Enclosure
Small 3D-printed housing for the Feather + LiPo with a slot that grips the
probe board head; cable runs inside. Designed after the board, as a separate
step.

## Cost estimate (2 sensors, before shipping)
- JLC: 5 PCBs + 2 assembled: setup $9.79 + Extended fees 3 x $3.09 + parts
  ~$13 + PCB ~$5 = **~$37**.
- 2 x Feather ESP32-C6 $29.90, 2 x LiPo ~$10, 2 x STEMMA QT cable ~$2.
- About **$80 before shipping for two**; the probe board drops to ~$4 each in
  later batches since setup and Extended fees are per order.

## Left to the builder
- Exact electrode geometry (interdigitated vs plate + shield), board outline
  details, and the FDC1004 CAPDAC default.
- KiCad symbol/footprint sources (KiCad 10 stock libs where possible).
- Which Basic 1 uF part.
- ESPHome external component structure.

## Risks
- FDC1004 stock at JLC is low (56 pcs of C2652097); if it runs out, the
  DSCJ (WSON-10, C2652081) variant is the fallback with a footprint change.
- Feather availability: out of stock at Adafruit; check DigiKey/Mouser/Pimoroni.
- Probe calibration varies with soil type; the YAML calibration handles it.
