create_clock -name Clock -period 62.500 [get_ports {Clock}]
derive_clock_uncertainty
set_false_path -from [get_ports {RESET_N}]
set_false_path -to [get_ports {LED}]
