# Enclosure

Two parts, outside 27.4 x 60.4 x 41 mm. Source: `enclosure.scad` (OpenSCAD).

- `base.stl` holds the battery side. The PCB sits on four corner pads that miss
  the battery holder and its tabs. Two keyholes in the back fit #4 / M3 screws.
- `lid.stl` covers the XIAO side. It has a 3 mm alignment lip with snap bumps,
  four posts that hold the PCB down, a USB-C opening, a slot over J3, and a
  divider wall plus vents that keep XIAO and charger heat away from the SHTC3.

## Printing (Bambu Studio)
- PETG (or ASA outdoors), 0.2 mm layers, 3 walls, 15 % infill.
- Base prints open side up. Lid STL is already flipped to print top-down.
- No supports needed. The USB opening and keyhole channel are short bridges.

## Measure before the final print
The stack heights are estimates. Measure your parts and change the values at
the top of `enclosure.scad`:
`socket_h` (SMD socket height, 8.5 mm guess), `spacer_h` (header spacer,
2.5 mm), `usb_h`. These set the lid height and where the USB-C hole sits.
Print the lid at 20 % infill first and test-fit the USB cable.

Re-export:
```bash
openscad -D 'part="base"' -o base.stl enclosure.scad
openscad -D 'part="lid"'  -o lid.stl  enclosure.scad
```
Options: `open_j3`, `open_j5`, `keyholes` (true/false).
