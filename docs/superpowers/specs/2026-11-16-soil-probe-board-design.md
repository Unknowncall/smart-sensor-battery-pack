# All-in-one soil sensor board: design

Date: 2026-11-16
Status: draft for approval

## Why

The owner wants battery soil sensors for their plants, reporting to Home
Assistant, made in house. The first board in this repo (XIAO on sockets,
BQ21040 charger, BQ29700 protection, TPS7A05 LDO) priced at about $122 for two
finished sensors, which is far too much for what it does. Commercial Zigbee
soil sensors sell for about $11. The goal is a board we design ourselves that
gets close to that per unit, with no hand soldering.

## Goals

- One PCB that is the whole sensor: ESP32-C6 radio/MCU, LiPo charging over
  USB-C, capacitive soil probe as copper traces on the board, air temperature
  and humidity, battery voltage.
- Fully assembled by JLCPCB (Economic PCBA, top side only). The owner only
  plugs in a battery and flashes firmware over USB-C.
- ESPHome over WiFi with deep sleep between readings.
- Minimum per-order JLC fees: use Basic and Preferred parts wherever they
  exist; only pay the $3.09 Extended fee where nothing else will do.

## Non-goals

- Zigbee firmware in v1 (the ESP32-C6 can do it later).
- Soil EC/fertility or light sensing.
- An on-board battery protection IC (see Battery).

## Anti-goals

- Anything the owner has to solder.
- Bare copper in the soil.
- A part that needs its own firmware or a programmer beyond USB-C.

## Constraints

- JLC Economic PCBA: top side only; needs HASL or LeadFree HASL (OSP blocks
  Economic). Setup $8.24 + stencil $1.55 per order; $3.09 per Extended part
  type; Basic and Preferred Extended parts have no per-part fee (verified
  against the earlier order: 11 non-Basic parts, 10 fees, the 11th was
  Preferred).
- No radio chip and no humidity sensor exists in JLC's Basic or Preferred
  lists (searched ESP32, nRF52840, Zigbee, BLE, SHT, AHT, HDC), so those cost
  a fee no matter what.

## Approaches considered

| | Approach | Why not / why |
|---|---|---|
| A | Keep the original XIAO battery board | ~$122 for two sensors; most parts Extended; needs hand-soldered holder |
| B | Buy Adafruit ESP32-C6 Feather ($14.95) + our own probe board on STEMMA QT | Still needs its own JLC order for the probe, so ~$80+ for two; Feather out of stock |
| **C (picked)** | One all-in-one board, Basic/Preferred parts first | ~$70 delivered for two, ~$7 per board in parts after that |

## Design

### Board
- 2-layer FR-4, 1.6 mm, LeadFree HASL, black. About 25 mm x 110 mm.
- **Head (top ~40 mm, above soil):** ESP32-C6-MINI-1 module with its antenna
  at the top edge and the module's copper keep-out honoured on both layers;
  USB-C on the top edge; JST-PH 2-pin battery connector; charger, regulator,
  passives; SHTC3 on a peninsula separated by a slot.
- **Probe (bottom ~70 mm, in soil):** sensing electrode traces with a ground
  return, fully under solder mask; no vias or exposed copper below the fill
  line; pointed tip. Silkscreen fill line marks max insertion depth.

### Circuit
- **USB-C (16-pin; 6-pin USB-C parts are power-only and can't flash):** 5V in, 5.1k CC pull-downs, D+/D- to the
  ESP32-C6's native USB (GPIO12/13) so ESPHome flashes and logs over the same
  port. No USB-UART chip.
- **Charging:** TP4056 from VBUS to the battery; charge current ~500 mA via
  RPROG; charge LED (Basic 0603).
- **Regulator:** XC6220 3.3 V (low quiescent current, handles WiFi TX peaks)
  from the battery, or from VBUS through the TP4056 when the battery is
  charging.
- **ESP32-C6:** EN RC delay; GPIO9 (boot strap) to a test pad for recovery
  only (esptool can enter download mode over native USB without a button).
- **Soil probe:** one GPIO drives a high-frequency PWM (ESP32 LEDC) through a
  series resistor into the probe electrode; the electrode-to-soil capacitance
  sets the amplitude; a 1N4148WS diode + RC peak detector turns that into a
  DC level read by an ADC pin. Same principle as the open-source b-parasite.
  All Basic parts. Exact values left to the builder; check b-parasite's
  licence before reusing its values.
- **Battery voltage:** divider from BAT to an ADC pin, high-value resistors
  (a few uA drain).
- **SHTC3** on I2C, powered from 3.3 V.

### Parts with a JLC fee (5 x $3.09)
| Part | LCSC | Unit |
|---|---|---|
| ESP32-C6-MINI-1-N4 | C5736265 | $4.10 |
| XC6220B331MR 3.3 V LDO | C3040644 | $0.20 |
| TYPE-C-31-M-12 USB-C, 16-pin (has D+/D-) | C165948 | $0.19 |
| JST-PH 2-pin SMD (exact part at layout) | e.g. C51940124 | ~$0.04 |
| SHTC3 | C194656 | $2.24 |

No-fee parts: TP4056 (C16581, Preferred), 1N4148WS (C2128, Basic), all
resistors, capacitors and the LED (Basic).

### Battery
- 1000 mAh LiPo with JST-PH 2.0 plug and a **built-in protection circuit**
  (stated by the seller). This replaces an on-board protection IC, which
  would add a fee. Polarity must match the board's silkscreen.
- Expected life on WiFi, a reading every 10 minutes: roughly 2 months per
  charge (estimate; to be measured).

### Firmware (ESPHome)
- Deep sleep 10 minutes; on wake: start PWM, settle, read soil ADC, stop
  PWM; read SHTC3; read battery ADC; publish; sleep.
- Moisture % from a two-point calibration (dry air, glass of water) in YAML.

### Enclosure
Separate step after the board: a small printed cap over the head that holds
the LiPo and leaves the antenna end clear.

## Cost estimate
- First JLC order, 5 PCBs + 2 assembled: setup $9.79 + fees $15.45 + PCBs ~$6
  + parts ~$14 = **~$45** before shipping. With shipping and 2 LiPos,
  **~$70 for two finished sensors**.
- Later orders: ~$7 per board in parts + ~$25 per order.

## Left to the builder
- Probe excitation frequency and RC/diode values; electrode geometry.
- Exact JST-PH SMD part, LED/resistor values, RPROG value.
- Board outline details and routing.

## Risks
- ESP32-C6-MINI-1-N4 stock at JLC: 4,785 on 2026-11-16.
- USB-C part stock: 516,975 (C165948), no concern.
- First-spin risk: a layout bug means another ~$25 order and ~2 weeks.
- Probe readings depend on soil type; calibration in YAML covers this.
