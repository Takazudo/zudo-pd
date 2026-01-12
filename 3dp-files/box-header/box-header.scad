// IDC box connector frame for pin headers - WITH CENTER DIVIDER
// Based on design by John Stäck 2018
// Licensed under Creative Commons Attribution Share-alike 4.0 (CC BY-SA 4.0)
// https://creativecommons.org/licenses/by-sa/4.0/
//
// Modifications:
// - Changed bottom_thickness to 0.5mm
// - Added center divider on bottom surface

//Number of pins in one row of connector (half number of total pins)
n_pins = 8;

//How much to increase size of things to allow for good fit
printer_fudge = 0.2;

//Standard pin pitch
pin_pitch = 2.54;

//Pin size from C5383092 datasheet (SQ.0.64)
pin_size = 0.64;

//Tight clearance for 3D printed plastic (press-fit)
tight_clearance = 0.2;

//Dimensions of IDC connector
connector_length = 5.4+pin_pitch*n_pins;
connector_width = 6.4;

//Size of pin header base holes - TIGHT FIT based on actual pin dimensions
//Length: pin span + pin size + clearance
base_length = pin_pitch*(n_pins-1) + pin_size + tight_clearance;  // 17.78 + 0.64 + 0.2 = 18.62mm
//Width of each slot
slot_width = 0.6;  // Adjusted after print test (0.4 was too tight)

//Size of orientation tab
tab_width=4.5;
tab_height=5.5; //Arbitrary number. Have no specs on this

//Height of standard IDC box header.
height=8.9;

//The height of a regular pin header plastic base
// MODIFIED: Changed from pin_pitch (2.54mm) to 0.5mm
bottom_thickness=0.5;


//These are default sizes for the outside of the box
/*
outside_length = 7.6+pin_pitch*n_pins;
outside_width = 8.8;
*/

//Outside dimensions, a bit thicker for more sturdiness when printed.
wall_thickness = 1.5;

outside_length = connector_length + 2*wall_thickness + printer_fudge;
outside_width = connector_width + 2*wall_thickness + printer_fudge;

conn_length_actual = connector_length + printer_fudge;
conn_width_actual = connector_width + printer_fudge;

tab_width_actual = tab_width + printer_fudge;

// ADDED: Center divider - calculated from row spacing minus slot widths
// Divider fills the gap between the two pin row slots
divider_thickness = pin_pitch - slot_width;  // 2.54 - 0.84 = 1.7mm


difference() {
    cube([outside_length, outside_width, height]);

    //All the things "cut out" are from center origin to make things easier to follow
    translate([outside_length/2, outside_width/2, 0]) {

        //Hole for connector (single open cavity above bottom plate)
        translate([-conn_length_actual/2, -conn_width_actual/2, bottom_thickness])
            cube([conn_length_actual, conn_width_actual, height]);

        //Hole for pin header in base - ROW 1 (tight slot for first pin row)
        // Centered at -pin_pitch/2 from center (Y offset = -1.27mm)
        translate([-base_length/2, -pin_pitch/2 - slot_width/2, -0.1])
            cube([base_length, slot_width, bottom_thickness + 0.2]);

        //Hole for pin header in base - ROW 2 (tight slot for second pin row)
        // Centered at +pin_pitch/2 from center (Y offset = +1.27mm)
        translate([-base_length/2, pin_pitch/2 - slot_width/2, -0.1])
            cube([base_length, slot_width, bottom_thickness + 0.2]);

        //Tab upper part (key notch for IDC connector) - extends from bottom plate to top
        translate([-tab_width_actual/2, -outside_width, bottom_thickness])
            cube([tab_width_actual, outside_width, height]);

        //Tab lower part (foot separator - only through the wall, not the bottom plate)
        translate([-tab_width_actual/2, -outside_width, -0.1])
            cube([tab_width_actual, outside_width/2 + wall_thickness, bottom_thickness + 0.2]);

    }

}
