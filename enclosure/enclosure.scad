// Smart Sensor Battery Pack - two-part enclosure
// Board: 23 x 56 mm, 1.6 mm, Keystone 1096 18350 holder on the back,
// XIAO ESP32-C6 on SMD sockets on the front, SHTC3 on the bottom-left tip.
//
// Coordinates: origin = board bottom-left corner seen from the top
// (KiCad x - 124, 111.5 - KiCad y). +Y points toward the J3 sensor socket,
// +X points toward the XIAO's USB-C port. Z = 0 is the board's bottom face.
//
// Render one part at a time:  part = "base" | "lid" | "both" | "assembly"

part = "assembly";

/* ---------- measure these on your real parts ---------- */
pcb_t        = 1.6;    // PCB thickness
batt_h       = 15.11;  // Keystone 1096 max height (datasheet)
socket_h     = 8.5;    // SMD female socket body height
spacer_h     = 2.5;    // plastic spacer on the XIAO's male headers
xiao_t       = 1.0;    // XIAO PCB thickness
usb_h        = 3.2;    // USB-C receptacle height on top of XIAO
/* ------------------------------------------------------ */

soil_exit    = true;   // cable exit through the J3 end wall (case stands J3-end down)
battery_door = true;   // screw-on door in the base floor to swap the 18350
open_j3      = false;  // slot in the lid top over J3 (for a module that sticks up)
open_j5      = false;  // slot over J5 (middle 5-pin header)
keyholes     = false;  // keyholes in the back (cannot be combined with the door)

wall   = 1.8;
clr    = 0.4;          // board-to-wall clearance
floor_t= (keyholes || battery_door) ? 4.0 : 1.6;

// battery door (x/y in board coordinates, z from the base's bottom face)
door_t   = 2.0;                       // door thickness = recess depth
door_open= [1.5, 7.0, 21.5, 49.0];    // through-hole the cell passes through
door_rec = [0.0, 4.5, 23.0, 55.5];    // recess the door sits in
door_gap = 0.15;
door_screw = [11.5, 53.2];            // M2 x 8 countersunk / self-tapping
tongue   = [7.0, 1.5, 16.0, 4.5];     // tab that hooks under the far end

// soil cable exit (J3 pins 1..5 span x 4.26..14.42)
soil_cx = 9.34;
soil_w  = 5.0;
soil_h  = 4.5;   // hole height above the base rim; size for your cable
gap_under_batt = 1.0;
lid_top_t = 1.6;
split_above_pcb = 4.0; // base walls end this far above the PCB top (lip stops 1 mm above the board)
lip_h  = 3.0;          // lid alignment lip depth
lip_t  = 1.2;
lip_clr= 0.15;
$fn = 40;

bw = 23; bl = 56;                       // board
iw = bw + 2*clr; il = bl + 2*clr;       // cavity
ow = iw + 2*wall; ol = il + 2*wall;     // outside

pcb_z0 = 0;                              // board bottom (local)
pcb_top= pcb_t;
base_z0= -(batt_h + gap_under_batt) - floor_t;   // outside bottom of base
split_z= pcb_top + split_above_pcb;
xiao_bot = pcb_top + socket_h + spacer_h;
xiao_top = xiao_bot + xiao_t + usb_h;
lid_inner_top = xiao_top + 2.5;
lid_z1 = lid_inner_top + lid_top_t;

// XIAO / USB-C
xiao_cy = 29.77;
usb_cz  = xiao_bot + xiao_t + usb_h/2;
usb_w = 11.0; usb_hh = 7.0;              // fits most USB-C plug overmolds

// cavity origin offset (cavity starts at -clr)
module rrect(x,y,h,r=1.5){
  translate([r,r,0]) linear_extrude(h) offset(r) square([x-2*r,y-2*r]);
}
module outer_shell(z0,z1){ translate([-clr-wall,-clr-wall,z0]) rrect(ow,ol,z1-z0,2.5); }
module cavity(z0,z1){ translate([-clr,-clr,z0]) rrect(iw,il,z1-z0,1); }

// ---------- BASE ----------
// PCB rests on corner pads that miss the battery-holder body and its
// solder tabs (tabs: x 7.6..14.4 at both ends).
pad_h = batt_h + gap_under_batt;  // from cavity floor up to PCB bottom
pads = [ [-clr,     -clr, 4.5+clr, 4.6+clr],   // bottom-left (stops before slot at x=4)
         [15.5,     -clr, bw-15.5+clr, 4.6+clr],
         [-clr,  51.4,    6.5+clr, bl-51.4+clr],
         [15.5,  51.4,    bw-15.5+clr, bl-51.4+clr] ];

module keyhole_cut(y){
  // back face slot: 4 mm shank, 8 mm head entry, head channel above
  translate([bw/2, y, base_z0-0.01]) {
    cylinder(d=8.2, h=1.6+0.02);
    translate([-2,0,0]) cube([4,8,1.6+0.02]);
    translate([0,0,1.6]) hull(){ cylinder(d=8.2,h=2.4-0.6); translate([0,8,0]) cylinder(d=8.2,h=2.4-0.6); }
  }
}

module rect_xy(r, z0, h){ translate([r[0], r[1], z0]) cube([r[2]-r[0], r[3]-r[1], h]); }

module door_cuts(){
  rect_xy(door_open, base_z0-1, floor_t+2);                       // cell passes through
  rect_xy(door_rec,  base_z0-1, door_t+1);                        // flush recess
  rect_xy([tongue[0]-0.3, tongue[1]-0.3, tongue[2]+0.3, door_rec[1]+0.1],
          base_z0+0.6, 1.2);                                      // undercut for the tab
  translate([door_screw[0], door_screw[1], base_z0+door_t-0.1])
    cylinder(d=1.6, h=floor_t-door_t+4-0.5);                      // M2 pilot, blind
}

module door(){
  difference(){
    union(){
      // 0.5 mm extra play at the tab end so the door can tilt in tab-first
      translate([door_rec[0]+door_gap, door_rec[1]+0.5, 0])
        cube([door_rec[2]-door_rec[0]-2*door_gap, door_rec[3]-door_rec[1]-0.5-door_gap, door_t]);
      translate([tongue[0], tongue[1], 0.7]) cube([tongue[2]-tongue[0], door_rec[1]-tongue[1]+1, 1.0]);
    }
    translate([door_screw[0], door_screw[1], -0.01]) {
      cylinder(d=2.4, h=door_t+0.02);
      cylinder(d1=4.4, d2=2.4, h=1.0);                            // countersink (outside face)
    }
    // finger grip lines near the screw end
    for (i=[0:2]) translate([3, door_rec[3]-8-i*1.6, -0.01]) cube([4, 0.6, 0.5]);
  }
}

module base(){
  difference(){
    outer_shell(base_z0, split_z);
    cavity(base_z0+floor_t, split_z+1);
    if (keyholes && !battery_door){ keyhole_cut(12); keyhole_cut(36); }
    if (battery_door) door_cuts();
    // snap grooves for lid bumps (long sides)
    for (x=[-clr-0.01, bw+clr+0.01]) for (y=[14,42])
      translate([x, y, split_z-lip_h+1.5]) rotate([0,90,0]) cylinder(d=1.6, h=1.2, center=true);
  }
  // PCB support pads
  for (p=pads) translate([p[0], p[1], base_z0+floor_t]) cube([p[2], p[3], pad_h]);
  // screw boss for the door (stays clear of the holder body, which ends at y=50.6)
  if (battery_door) difference(){
    translate([door_screw[0], door_screw[1], base_z0+floor_t-0.01]) cylinder(d=4.6, h=4);
    translate([door_screw[0], door_screw[1], base_z0]) cylinder(d=1.6, h=floor_t+4-0.5);
  }
}

// ---------- LID ----------
module lid(){
  difference(){
    union(){
      outer_shell(split_z, lid_z1);
      // alignment lip that drops into the base
      translate([0,0,split_z-lip_h]) difference(){
        translate([-clr+lip_clr,-clr+lip_clr,0]) rrect(iw-2*lip_clr, il-2*lip_clr, lip_h, 1);
        translate([-clr+lip_clr+lip_t,-clr+lip_clr+lip_t,-0.1]) rrect(iw-2*lip_clr-2*lip_t, il-2*lip_clr-2*lip_t, lip_h+0.2, 0.5);
      }
    }
    cavity(split_z-0.01, lid_inner_top);   // lip below split_z keeps its own hollow
    // USB-C port (+X wall)
    translate([bw-1, xiao_cy-usb_w/2, usb_cz-usb_hh/2]) cube([wall+clr+3, usb_w, usb_hh]);
    // lip relief around the USB end
    translate([bw-2, xiao_cy-usb_w/2-1, split_z-lip_h-1]) cube([5, usb_w+2, lip_h+1.01]);
    // soil cable exit: notch in the J3 end wall + lip, closed underneath by the base rim
    if (soil_exit)
      translate([soil_cx-soil_w/2, bl-1, split_z-lip_h-1]) cube([soil_w, clr+wall+3, lip_h+1+soil_h]);
    // J3 sensor slot (top)
    if (open_j3) translate([2.5, 50.0, lid_inner_top-1]) cube([14, 6.4, lid_top_t+2]);
    if (open_j5) translate([5.0, 12.0, lid_inner_top-1]) cube([15, 7, lid_top_t+2]);
    // SHTC3 vents: top + left wall + bottom wall, all in the sealed-off tip
    for (x=[0.5:1.8:5.9]) translate([x, -0.2, lid_inner_top-1]) cube([0.9, 6.0, lid_top_t+2]);
    for (z=[split_z+1.5 : 2.2 : lid_inner_top-1.5])
      translate([-clr-wall-1, 0.3, z]) cube([wall+2, 5.4, 1.1]);
    for (z=[split_z+1.5 : 2.2 : lid_inner_top-1.5])
      translate([0.3, -clr-wall-1, z]) cube([6.0, wall+2, 1.1]);
    for (x=[0.3:1.8:6]) translate([x, -clr-lip_clr-lip_t-0.5, split_z-lip_h-0.5]) cube([0.9, lip_t+1, lip_h+0.6]);
  }
  // divider wall keeps XIAO/regulator heat away from the SHTC3
  translate([-clr+lip_clr, 6.2, pcb_top+1.5]) cube([iw-2*lip_clr, 1.2, lid_inner_top-pcb_top-1.5+0.01]);
  // posts that press the PCB onto the base pads (clear of all parts)
  for (p=[[1.2,54.5],[21.8,45.5],[21.8,4.5],[1.2,46]])
    translate([p[0],p[1],pcb_top+0.1]) cylinder(d=2.0, h=lid_inner_top-pcb_top-0.1+0.01);
  // snap bumps on the lip
  for (x=[-clr+lip_clr, bw+clr-lip_clr]) for (y=[14,42])
    translate([x, y, split_z-lip_h+1.5]) sphere(d=1.2);
}

// ---------- reference geometry for the assembly view ----------
module board_ghost(){
  color("green", 0.6) difference(){
    cube([bw, bl, pcb_t]);
    translate([4,-1,-1]) cube([2,6,4]);         // sensor isolation slot
    translate([-1,4.75,-1]) cube([2.5,2,4]);    // notch
  }
  color("dimgray",0.7) translate([0.42, 5.4, -batt_h]) cube([21.15, 45.2, batt_h]);
  color("royalblue",0.7) translate([1.46, xiao_cy-8.9, xiao_bot]) cube([21, 17.8, xiao_t]);
  color("silver") translate([bw-7.3, xiao_cy-4.5, xiao_bot+xiao_t]) cube([7.5, 9, usb_h]);
  color("black") for (y=[22.15, 37.39]) translate([1.46+2.9, y-1.27, pcb_top]) cube([15.24, 2.54, socket_h]);
}

if (part=="base") base();
else if (part=="lid") translate([0,bl,lid_z1]) rotate([180,0,0]) lid();   // printed top-down
else if (part=="door") door();            // print outside face down
else if (part=="none") {}                 // for include-based fit checks
else if (part=="both"){ base(); translate([ow+8, bl, lid_z1]) rotate([180,0,0]) lid();
                        translate([2*ow+16, 0, base_z0]) door(); }
else { color("lightgray") base(); color("white",0.5) lid(); board_ghost();
       if (battery_door) color("orange") translate([0,0,base_z0]) door(); }

echo(str("Outside: ", ow, " x ", ol, " x ", lid_z1-base_z0, " mm"));
echo(str("XIAO bottom ", xiao_bot, " / top ", xiao_top, " above PCB bottom; USB centre z ", usb_cz));
