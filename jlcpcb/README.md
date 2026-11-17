# JLCPCB order files

Generated with kicad-cli 10.0.8 from `smart_sensor_battery.kicad_pcb`. DRC: 0 violations, 0 unconnected.

| File | Upload where |
|---|---|
| `smart_sensor_battery-gerbers.zip` | "Add gerber file" |
| `BOM-JLCPCB.csv` | PCB Assembly -> BOM |
| `CPL-JLCPCB.csv` | PCB Assembly -> CPL / pick-and-place |

## Order settings
- 2 layers, 1.6 mm, 23 x 56 mm (JLC detects it from the outline)
- PCB Assembly: **Economic**, **Top side** only
- Every part is on the top side except BT1 (battery holder, bottom), and BT1 is
  intentionally left out of the BOM/CPL. Buy a Keystone 1096 from Mouser/DigiKey
  and hand-solder its two big SMD tabs.

## BOM notes
- U7 SHTC3 had no LCSC number in the schematic. `C194656` (Sensirion
  SHTC3-TR-2.5KS, DFN-4-EP 2x2) was added here; it was in stock at JLC on 2026-11-16.
- Extended parts (about $3 setup fee each): J1/J2/J3 sockets C42379199, J5 socket
  C42379198, BQ21040 C202311, TPS7A0533 C493453, BQ29700 C183096,
  CSD85301Q2 C544396, SHTC3 C194656.
- J3 uses the 7-pin socket part on purpose (the footprint is 7-pin). J1, J2
  and J3 are on one BOM line; as separate lines JLC unticks them with a
  "multiple lines matched to the same part" warning.
- Economic PCBA is greyed out when the surface finish is OSP (the quote page
  default in Nov 2026). Pick HASL or LeadFree HASL first.
- Quote on 2026-11-16: 5 boards, black, LeadFree HASL, Economic PCBA top side,
  Confirm Parts Placement on = $74.00 before shipping.

## Before you pay
Check every part's rotation and pin 1 in JLC's placement preview. KiCad and JLC
disagree on rotation for some packages; SOT-23 (Q1), SOT-23-5/6 (U4, U2), the
WSON-6 (U5), the CSD85301Q2 (U6) and the LED (D1) are the ones to look at.
