set hd $::env(PDKPATH)/libs.ref/sky130_fd_sc_hd
file copy -force $hd/techlef/sky130_fd_sc_hd.tlef build/technology.tlef
read_lef build/technology.tlef
read_lef -library $hd/lef/sky130_fd_sc_hd.lef
read_liberty $hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog build/mapped.v
link_design register8
initialize_floorplan -die_area {0 0 40 40} -core_area {5 5 35 35} -site unithd
create_clock -name core -period 20 [get_ports clk]
set_wire_rc -signal -resistance 0.1 -capacitance 0.1
set_dft_config -max_length 8 -max_chains 1 -clock_mixing no_mix \
    -scan_enable_name_pattern scan_enable -scan_in_name_pattern scan_in -scan_out_name_pattern scan_out
report_dft_config
scan_replace
global_placement -skip_io -density 0.30
report_dft_plan -verbose
execute_dft_plan
write_verilog build/inserted.v
write_db build/inserted.odb
write_def build/inserted.def
puts "DFT_INSERTION_FINISHED"
