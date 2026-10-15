def apply_instrumentation():
    with open("scanner_mtf_backtest_lab.pine", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add alternative pivots and autopsy variables near vis_last_ph
    autopsy_vars = """var float vis_prev_pl = na

// --- AUTOPSIE SWEEP ---
var int dbg_sweep_time = na
var string dbg_sweep_dir = ""
var float dbg_sweep_px = na
var float dbg_sweep_liq = na
var float dbg_mss_55 = na
var float dbg_mss_33 = na
var float dbg_mss_22 = na
var float dbg_sweep_atr = na
var string dbg_death_reason = ""
var float dbg_max_reach = na
var bool dbg_crossed_55_close = false
var bool dbg_crossed_55_nodisp = false

// Alternative pivots
ph_33 = ta.pivothigh(high, 3, 3)
pl_33 = ta.pivotlow(low, 3, 3)
var float vis_last_ph_33 = na
var float vis_last_pl_33 = na
if not na(ph_33)
    vis_last_ph_33 := ph_33
if not na(pl_33)
    vis_last_pl_33 := pl_33

ph_22 = ta.pivothigh(high, 2, 2)
pl_22 = ta.pivotlow(low, 2, 2)
var float vis_last_ph_22 = na
var float vis_last_pl_22 = na
if not na(ph_22)
    vis_last_ph_22 := ph_22
if not na(pl_22)
    vis_last_pl_22 := pl_22"""
    content = content.replace("var float vis_prev_pl = na", autopsy_vars)

    # 2. Add capture logic to BUY resets
    resets_buy_old = """if buy_state != STATE_IDLE
    if not na(buy_sweep_low) and low < buy_sweep_low
        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE
    else if sweep_h
        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE
    else if buy_state == STATE_SWEEP_ARMED and (bar_index - buy_sweep_bar > MAX_BARS_SWEEP_TO_MSS)
        buy_state := STATE_IDLE
    else if (buy_state == STATE_CAUSAL_FVG_CONFIRMED) and not na(buy_ob_bot) and close < buy_ob_bot
        buy_state := STATE_IDLE
    else if h1_bull_consumed
        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE"""
        
    resets_buy_new = """if buy_state != STATE_IDLE
    if not na(buy_sweep_low) and low < buy_sweep_low
        if buy_state == STATE_SWEEP_ARMED and dbg_death_reason == "PENDING"
            dbg_death_reason := "SL Structurel (low < sweep)"
        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE
    else if sweep_h
        if buy_state == STATE_SWEEP_ARMED and dbg_death_reason == "PENDING"
            dbg_death_reason := "Sweep opposé (sweep_h)"
        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE
    else if buy_state == STATE_SWEEP_ARMED and (bar_index - buy_sweep_bar > MAX_BARS_SWEEP_TO_MSS)
        if dbg_death_reason == "PENDING"
            dbg_death_reason := "Expiration 18 barres"
        buy_state := STATE_IDLE
    else if (buy_state == STATE_CAUSAL_FVG_CONFIRMED) and not na(buy_ob_bot) and close < buy_ob_bot
        buy_state := STATE_IDLE
    else if h1_bull_consumed
        if buy_state == STATE_SWEEP_ARMED and dbg_death_reason == "PENDING"
            dbg_death_reason := "H1 POI consommé"
        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE"""
    content = content.replace(resets_buy_old, resets_buy_new)

    # 3. Add capture logic to BUY transitions
    trans_buy_old = """if buy_state == STATE_IN_POI
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
else if buy_state == STATE_SWEEP_ARMED
    if sweep_l
        buy_sweep_bar := bar_index
        buy_sweep_low := low
        buy_mss_level := vis_last_ph
    else if bar_confirmed and not na(buy_mss_level) and close > buy_mss_level and close > open and is_disp_quant
        buy_state            := STATE_MSS_CONFIRMED"""
        
    trans_buy_new = """if buy_state == STATE_IN_POI
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
        
        dbg_sweep_time := time
        dbg_sweep_dir := "BUY"
        dbg_sweep_px := low
        dbg_sweep_liq := vis_last_pl
        dbg_mss_55 := vis_last_ph
        dbg_mss_33 := vis_last_ph_33
        dbg_mss_22 := vis_last_ph_22
        dbg_sweep_atr := atr_val[1]
        dbg_death_reason := "PENDING"
        dbg_max_reach := high
        dbg_crossed_55_close := false
        dbg_crossed_55_nodisp := false

    else if bar_index - buy_poi_bar >= 20 or h1_bull_consumed
        buy_state := STATE_IDLE
else if buy_state == STATE_SWEEP_ARMED
    if dbg_death_reason == "PENDING"
        dbg_max_reach := math.max(dbg_max_reach, high)
        if bar_confirmed and not na(buy_mss_level) and close > buy_mss_level
            dbg_crossed_55_close := true
            if not (close > open and is_disp_quant)
                dbg_crossed_55_nodisp := true

    if sweep_l
        buy_sweep_bar := bar_index
        buy_sweep_low := low
        buy_mss_level := vis_last_ph
        
        dbg_sweep_time := time
        dbg_sweep_dir := "BUY"
        dbg_sweep_px := low
        dbg_sweep_liq := vis_last_pl
        dbg_mss_55 := vis_last_ph
        dbg_mss_33 := vis_last_ph_33
        dbg_mss_22 := vis_last_ph_22
        dbg_sweep_atr := atr_val[1]
        dbg_death_reason := "PENDING"
        dbg_max_reach := high
        dbg_crossed_55_close := false
        dbg_crossed_55_nodisp := false

    else if bar_confirmed and not na(buy_mss_level) and close > buy_mss_level and close > open and is_disp_quant
        if dbg_death_reason == "PENDING"
            dbg_death_reason := "SUCCESS (MSS_CONFIRMED)"
        buy_state            := STATE_MSS_CONFIRMED"""
    content = content.replace(trans_buy_old, trans_buy_new)


    # 4. SELL resets
    resets_sell_old = """if sell_state != STATE_IDLE
    if not na(sell_sweep_high) and high > sell_sweep_high
        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
            cnt_sell_limit_cancel += 1
        sell_state := STATE_IDLE
    else if sweep_l
        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
            cnt_sell_limit_cancel += 1
        sell_state := STATE_IDLE
    else if sell_state == STATE_SWEEP_ARMED and (bar_index - sell_sweep_bar > MAX_BARS_SWEEP_TO_MSS)
        sell_state := STATE_IDLE
    else if (sell_state == STATE_CAUSAL_FVG_CONFIRMED) and not na(sell_ob_top) and close > sell_ob_top
        sell_state := STATE_IDLE
    else if h1_bear_consumed
        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
            cnt_sell_limit_cancel += 1
        sell_state := STATE_IDLE"""
        
    resets_sell_new = """if sell_state != STATE_IDLE
    if not na(sell_sweep_high) and high > sell_sweep_high
        if sell_state == STATE_SWEEP_ARMED and dbg_death_reason == "PENDING"
            dbg_death_reason := "SL Structurel (high > sweep)"
        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
            cnt_sell_limit_cancel += 1
        sell_state := STATE_IDLE
    else if sweep_l
        if sell_state == STATE_SWEEP_ARMED and dbg_death_reason == "PENDING"
            dbg_death_reason := "Sweep opposé (sweep_l)"
        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
            cnt_sell_limit_cancel += 1
        sell_state := STATE_IDLE
    else if sell_state == STATE_SWEEP_ARMED and (bar_index - sell_sweep_bar > MAX_BARS_SWEEP_TO_MSS)
        if dbg_death_reason == "PENDING"
            dbg_death_reason := "Expiration 18 barres"
        sell_state := STATE_IDLE
    else if (sell_state == STATE_CAUSAL_FVG_CONFIRMED) and not na(sell_ob_top) and close > sell_ob_top
        sell_state := STATE_IDLE
    else if h1_bear_consumed
        if sell_state == STATE_SWEEP_ARMED and dbg_death_reason == "PENDING"
            dbg_death_reason := "H1 POI consommé"
        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
            cnt_sell_limit_cancel += 1
        sell_state := STATE_IDLE"""
    content = content.replace(resets_sell_old, resets_sell_new)

    # 5. SELL transitions
    trans_sell_old = """if sell_state == STATE_IN_POI
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
else if sell_state == STATE_SWEEP_ARMED
    if sweep_h
        sell_sweep_bar := bar_index
        sell_sweep_high := high
        sell_mss_level := vis_last_pl
    else if bar_confirmed and not na(sell_mss_level) and close < sell_mss_level and close < open and is_disp_quant
        sell_state            := STATE_MSS_CONFIRMED"""

    trans_sell_new = """if sell_state == STATE_IN_POI
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
        
        dbg_sweep_time := time
        dbg_sweep_dir := "SELL"
        dbg_sweep_px := high
        dbg_sweep_liq := vis_last_ph
        dbg_mss_55 := vis_last_pl
        dbg_mss_33 := vis_last_pl_33
        dbg_mss_22 := vis_last_pl_22
        dbg_sweep_atr := atr_val[1]
        dbg_death_reason := "PENDING"
        dbg_max_reach := low
        dbg_crossed_55_close := false
        dbg_crossed_55_nodisp := false

    else if bar_index - sell_poi_bar >= 20 or h1_bear_consumed
        sell_state := STATE_IDLE
else if sell_state == STATE_SWEEP_ARMED
    if dbg_death_reason == "PENDING"
        dbg_max_reach := math.min(dbg_max_reach, low)
        if bar_confirmed and not na(sell_mss_level) and close < sell_mss_level
            dbg_crossed_55_close := true
            if not (close < open and is_disp_quant)
                dbg_crossed_55_nodisp := true

    if sweep_h
        sell_sweep_bar := bar_index
        sell_sweep_high := high
        sell_mss_level := vis_last_pl
        
        dbg_sweep_time := time
        dbg_sweep_dir := "SELL"
        dbg_sweep_px := high
        dbg_sweep_liq := vis_last_ph
        dbg_mss_55 := vis_last_pl
        dbg_mss_33 := vis_last_pl_33
        dbg_mss_22 := vis_last_pl_22
        dbg_sweep_atr := atr_val[1]
        dbg_death_reason := "PENDING"
        dbg_max_reach := low
        dbg_crossed_55_close := false
        dbg_crossed_55_nodisp := false

    else if bar_confirmed and not na(sell_mss_level) and close < sell_mss_level and close < open and is_disp_quant
        if dbg_death_reason == "PENDING"
            dbg_death_reason := "SUCCESS (MSS_CONFIRMED)"
        sell_state            := STATE_MSS_CONFIRMED"""
    content = content.replace(trans_sell_old, trans_sell_new)


    # 6. Build the table display logic
    table_logic = """
    // COLONNE 4: AUTOPSIE SWEEP
    table.cell(dbg, 4, 0, "AUTOPSIE DU DERNIER SWEEP", text_color=color.orange, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 5, 0, "", bgcolor=color.new(color.black,15))
    
    table.cell(dbg, 4, 1, "Sens", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 5, 1, dbg_sweep_dir, text_color=color.white, text_size=size.small, text_halign=text.align_right)
    
    time_str = na(dbg_sweep_time) ? "-" : str.format_time(dbg_sweep_time, "MM-dd HH:mm", "America/New_York")
    table.cell(dbg, 4, 2, "Date (New York)", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 5, 2, time_str, text_color=color.white, text_size=size.small, text_halign=text.align_right)

    table.cell(dbg, 4, 3, "Prix Sweep", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 5, 3, str.tostring(dbg_sweep_px), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    
    if dbg_sweep_dir == "BUY"
        dist_55 = na(dbg_mss_55) or na(dbg_sweep_px) ? na : (dbg_mss_55 - dbg_sweep_px) / dbg_sweep_atr
        dist_33 = na(dbg_mss_33) or na(dbg_sweep_px) ? na : (dbg_mss_33 - dbg_sweep_px) / dbg_sweep_atr
        dist_22 = na(dbg_mss_22) or na(dbg_sweep_px) ? na : (dbg_mss_22 - dbg_sweep_px) / dbg_sweep_atr
        
        table.cell(dbg, 4, 4, "Niveau MSS 5/5", text_color=color.white, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 4, str.tostring(dbg_mss_55) + " (" + str.tostring(dist_55, "#.#") + "a)", text_color=color.white, text_size=size.small, text_halign=text.align_right)
        
        table.cell(dbg, 4, 5, "Niveau MSS 3/3", text_color=color.silver, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 5, str.tostring(dbg_mss_33) + " (" + str.tostring(dist_33, "#.#") + "a)", text_color=color.silver, text_size=size.small, text_halign=text.align_right)
        
        table.cell(dbg, 4, 6, "Niveau MSS 2/2", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 6, str.tostring(dbg_mss_22) + " (" + str.tostring(dist_22, "#.#") + "a)", text_color=color.gray, text_size=size.small, text_halign=text.align_right)
        
        table.cell(dbg, 4, 7, "Plus haut atteint", text_color=color.white, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 7, str.tostring(dbg_max_reach), text_color=color.white, text_size=size.small, text_halign=text.align_right)
        
    else if dbg_sweep_dir == "SELL"
        dist_55 = na(dbg_mss_55) or na(dbg_sweep_px) ? na : (dbg_sweep_px - dbg_mss_55) / dbg_sweep_atr
        dist_33 = na(dbg_mss_33) or na(dbg_sweep_px) ? na : (dbg_sweep_px - dbg_mss_33) / dbg_sweep_atr
        dist_22 = na(dbg_mss_22) or na(dbg_sweep_px) ? na : (dbg_sweep_px - dbg_mss_22) / dbg_sweep_atr
        
        table.cell(dbg, 4, 4, "Niveau MSS 5/5", text_color=color.white, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 4, str.tostring(dbg_mss_55) + " (" + str.tostring(dist_55, "#.#") + "a)", text_color=color.white, text_size=size.small, text_halign=text.align_right)
        
        table.cell(dbg, 4, 5, "Niveau MSS 3/3", text_color=color.silver, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 5, str.tostring(dbg_mss_33) + " (" + str.tostring(dist_33, "#.#") + "a)", text_color=color.silver, text_size=size.small, text_halign=text.align_right)
        
        table.cell(dbg, 4, 6, "Niveau MSS 2/2", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 6, str.tostring(dbg_mss_22) + " (" + str.tostring(dist_22, "#.#") + "a)", text_color=color.gray, text_size=size.small, text_halign=text.align_right)
        
        table.cell(dbg, 4, 7, "Plus bas atteint", text_color=color.white, text_size=size.small, text_halign=text.align_left)
        table.cell(dbg, 5, 7, str.tostring(dbg_max_reach), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg, 4, 8, "Franchissement Clôture ?", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 5, 8, dbg_crossed_55_close ? "OUI" : "NON", text_color=dbg_crossed_55_close ? color.lime : color.gray, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg, 4, 9, "Échec par manque de Disp ?", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 5, 9, dbg_crossed_55_nodisp ? "OUI" : "NON", text_color=dbg_crossed_55_nodisp ? color.red : color.gray, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg, 4, 10, "Raison de sortie/mort", text_color=color.orange, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 5, 10, dbg_death_reason, text_color=color.orange, text_size=size.small, text_halign=text.align_right)
"""

    content = content.replace("table.cell(dbg, 3, 19, str.tostring(cnt_sell_expired_limit), text_color=color.gray, text_size=size.small, text_halign=text.align_right)", 
                              "table.cell(dbg, 3, 19, str.tostring(cnt_sell_expired_limit), text_color=color.gray, text_size=size.small, text_halign=text.align_right)\n" + table_logic)


    # Don't forget to expand the table size to handle columns 4 and 5 (width 6, height 20)
    content = content.replace("var table dbg = table.new(position.top_right, 4, 25", "var table dbg = table.new(position.top_right, 6, 25")

    with open("scanner_mtf_backtest_lab.pine", "w", encoding="utf-8") as f:
        f.write(content)

apply_instrumentation()
