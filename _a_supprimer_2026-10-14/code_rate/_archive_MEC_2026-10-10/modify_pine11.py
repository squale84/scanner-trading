def apply_fixes():
    with open("scanner_mtf_backtest_lab.pine", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. C2: Add buy_poi_bar and sell_poi_bar declarations
    m5_vars = """var int   buy_limit_bar        = na
var int   buy_poi_bar          = na"""
    content = content.replace("var int   buy_limit_bar        = na", m5_vars)

    m5_vars_sell = """var int   sell_limit_bar        = na
var int   sell_poi_bar          = na"""
    content = content.replace("var int   sell_limit_bar        = na", m5_vars_sell)

    # 2. C3: Separate `if` for STATE_IN_POI and C2: Expiration 20 bars
    # Original BUY transition:
    old_buy_trans = """if buy_state == STATE_IDLE
    if in_h1_bull_zone
        buy_state := STATE_IN_POI
        cnt_buy_in_poi += 1
else if buy_state == STATE_IN_POI
    if sweep_l
        buy_state            := STATE_SWEEP_ARMED
        buy_sweep_bar        := bar_index
        buy_sweep_low        := low
        buy_mss_level        := vis_last_ph
        buy_displacement_bar := na
        buy_fvg_top          := na
        buy_fvg_bottom       := na
        buy_fvg_bar          := na
        buy_ob_top           := na
        buy_ob_bot           := na
        buy_limit_bar        := na
        cnt_sweep_l += 1
    else if not in_h1_bull_zone
        buy_state := STATE_IDLE
else if buy_state == STATE_SWEEP_ARMED"""

    new_buy_trans = """if buy_state == STATE_IDLE
    if in_h1_bull_zone
        buy_state := STATE_IN_POI
        buy_poi_bar := bar_index
        cnt_buy_in_poi += 1

if buy_state == STATE_IN_POI
    if sweep_l
        buy_state            := STATE_SWEEP_ARMED
        buy_sweep_bar        := bar_index
        buy_sweep_low        := low
        buy_mss_level        := vis_last_ph
        buy_displacement_bar := na
        buy_fvg_top          := na
        buy_fvg_bottom       := na
        buy_fvg_bar          := na
        buy_ob_top           := na
        buy_ob_bot           := na
        buy_limit_bar        := na
        cnt_sweep_l += 1
    else if bar_index - buy_poi_bar >= 20 or h1_bull_consumed
        buy_state := STATE_IDLE
else if buy_state == STATE_SWEEP_ARMED"""

    content = content.replace(old_buy_trans, new_buy_trans)

    # 3. Centralize C1 BUY cleanup
    buy_cleanup = """        buy_state := STATE_IDLE
        cnt_buy_expired_limit += 1

if buy_state == STATE_IDLE
    buy_sweep_low := na

// -------------------------------------------------------------"""
    content = content.replace("""        buy_state := STATE_IDLE
        cnt_buy_expired_limit += 1

// -------------------------------------------------------------""", buy_cleanup)


    # 4. SELL Transitions
    old_sell_trans = """if sell_state == STATE_IDLE
    if in_h1_bear_zone
        sell_state := STATE_IN_POI
        cnt_sell_in_poi += 1
else if sell_state == STATE_IN_POI
    if sweep_h
        sell_state            := STATE_SWEEP_ARMED
        sell_sweep_bar        := bar_index
        sell_sweep_high       := high
        sell_mss_level        := vis_last_pl
        sell_displacement_bar := na
        sell_fvg_top          := na
        sell_fvg_bottom       := na
        sell_fvg_bar          := na
        sell_ob_top           := na
        sell_ob_bot           := na
        sell_limit_bar        := na
        cnt_sweep_h += 1
    else if not in_h1_bear_zone
        sell_state := STATE_IDLE
else if sell_state == STATE_SWEEP_ARMED"""

    new_sell_trans = """if sell_state == STATE_IDLE
    if in_h1_bear_zone
        sell_state := STATE_IN_POI
        sell_poi_bar := bar_index
        cnt_sell_in_poi += 1

if sell_state == STATE_IN_POI
    if sweep_h
        sell_state            := STATE_SWEEP_ARMED
        sell_sweep_bar        := bar_index
        sell_sweep_high       := high
        sell_mss_level        := vis_last_pl
        sell_displacement_bar := na
        sell_fvg_top          := na
        sell_fvg_bottom       := na
        sell_fvg_bar          := na
        sell_ob_top           := na
        sell_ob_bot           := na
        sell_limit_bar        := na
        cnt_sweep_h += 1
    else if bar_index - sell_poi_bar >= 20 or h1_bear_consumed
        sell_state := STATE_IDLE
else if sell_state == STATE_SWEEP_ARMED"""

    content = content.replace(old_sell_trans, new_sell_trans)

    # 5. Centralize C1 SELL cleanup
    sell_cleanup = """        sell_state := STATE_IDLE
        cnt_sell_expired_limit += 1

if sell_state == STATE_IDLE
    sell_sweep_high := na

// ---- LAB B7.2"""
    content = content.replace("""        sell_state := STATE_IDLE
        cnt_sell_expired_limit += 1

// ---- LAB B7.2""", sell_cleanup)

    # 6. Safety check for the raw_buy resets, they also need to clean up because they occur outside the main state machine block.
    # Actually, we can just put a global cleanup at the very end of the script for safety, but placing it where we did is good for the state machine.
    # However, raw_buy and raw_sell also set state to IDLE.
    # Let's add the cleanup directly to the raw_buy/raw_sell blocks for safety.
    
    content = content.replace("buy_state := STATE_IDLE\n            cnt_buy_sl_invalid", "buy_state := STATE_IDLE\n            buy_sweep_low := na\n            cnt_buy_sl_invalid")
    content = content.replace("buy_state := STATE_IDLE\n                cnt_buy_no_target", "buy_state := STATE_IDLE\n                buy_sweep_low := na\n                cnt_buy_no_target")

    content = content.replace("sell_state := STATE_IDLE\n            cnt_sell_sl_invalid", "sell_state := STATE_IDLE\n            sell_sweep_high := na\n            cnt_sell_sl_invalid")
    content = content.replace("sell_state := STATE_IDLE\n                cnt_sell_no_target", "sell_state := STATE_IDLE\n                sell_sweep_high := na\n                cnt_sell_no_target")


    with open("scanner_mtf_backtest_lab.pine", "w", encoding="utf-8") as f:
        f.write(content)

apply_fixes()
