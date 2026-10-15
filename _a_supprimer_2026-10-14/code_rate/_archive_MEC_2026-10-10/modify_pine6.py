import re

with open("scanner_mtf_backtest_lab.pine", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the declarations from their original place
declarations = """var bool   in_pos       = false
var float  pos_entry    = 0.0
var float  pos_sl       = 0.0
var float  pos_tp       = 0.0
var string pos_dir      = "NONE"
var int    last_sig_bar = 0"""

content = content.replace(declarations + "\n", "")

# Insert them just before the state definitions
state_definitions = "int STATE_IDLE                = 0"
new_state_definitions = declarations + "\n\n" + state_definitions

content = content.replace(state_definitions, new_state_definitions)

with open("scanner_mtf_backtest_lab.pine", "w", encoding="utf-8") as f:
    f.write(content)
