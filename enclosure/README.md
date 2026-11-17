# Enclosure

Three printed parts, outside 27.4 x 60.4 x 41 mm. Source: `enclosure.scad` (OpenSCAD).

Meant to stand upright with the **J3 end down** (toward the soil). The SHTC3
vents then face up, away from wet dirt, and the soil-sensor cable leaves
through the bottom end wall.

- `base.stl` holds the battery side. The PCB sits on four corner pads that miss
  the 18350 holder and its tabs. The floor has an opening the cell passes
  through, a recess for the door, an undercut for the door's tab, and a screw boss.
- `door.stl` is the battery door. Hook its tab into the slot at the SHTC3 end,
  swing it flat, and fix it with one **M2 x 8 countersunk self-tapping screw**.
  Remove the door to pull the cell out of the holder without opening the case.
- `lid.stl` covers the XIAO side: alignment lip with snap bumps, four posts that
  hold the PCB down, USB-C opening, a 5 x 4.5 mm cable exit in the J3 end wall
  (closed underneath by the base rim), and a divider wall plus vents that keep
  XIAO/charger heat away from the SHTC3.

## Soil sensor wiring
Plug the sensor cable's male header into J3 (3V, NC, GND, SCL, SDA), run it
down the inside of the end wall, and out the notch. Put the lid on over the
cable. Add a knot or a dab of hot glue inside as strain relief. Make `soil_h`
and `soil_w` bigger in `enclosure.scad` if your cable is thicker than 4.5 mm.

## Printing (Bambu Studio)
- PETG (or ASA outdoors), 0.2 mm layers, 3 walls, 15 % infill.
- Base prints open side up. Lid STL is already flipped to print top-down.
  Door prints outside face down.
- No supports needed. The USB opening and the door-tab slot are short bridges.

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
openscad -D 'part="door"' -o door.stl enclosure.scad
```
Options: `soil_exit`, `battery_door`, `open_j3`, `open_j5`, `keyholes`
(keyholes only work with `battery_door = false`).

Fit check (each should print only contact faces, the hold-down posts, or "empty"):
`intersection(){ lid(); cube([bw,bl,pcb_t+0.8]); }` and
`intersection(){ base(); translate([0.42,5.4,-batt_h]) cube([21.15,45.2,batt_h]); }`
with `include <enclosure.scad>` and `-D 'part="none"'`.
