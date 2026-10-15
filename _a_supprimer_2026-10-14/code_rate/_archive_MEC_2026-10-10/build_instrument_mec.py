import os

def build_fixed_instrumentation():
    with open('scanner_mtf_backtest_mec.pine', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out_lines = []
    for i, line in enumerate(lines):
        if "// --- MEC FUNCTIONS ---" in line:
            out_lines = lines[:i]
            break

    instrumented_logic = """// --- MEC FUNCTIONS ---
f_mec_get_impulse_buy(mss_lvl, atr_ref) =>
    int start_idx = 0
    bool valid = false
    
    if close > mss_lvl
        float b1 = math.max(0, close - open)
        float b2 = math.max(0, close[1] - open[1])
        float b3 = math.max(0, close[2] - open[2])
        
        float d_net1 = close - open
        float d_tot1 = high - low
        float eff1 = d_tot1 > 0 ? (d_net1 / d_tot1) : 0
        if b1 >= mec_disp_atr_min * atr_ref and eff1 >= mec_disp_eff_min
            valid := true
            start_idx := 0
            
        if not valid
            float d_net2 = close - open[1]
            float d_tot2 = math.max(high, high[1]) - math.min(low, low[1])
            float eff2 = d_tot2 > 0 ? (d_net2 / d_tot2) : 0
            if (b1 + b2) >= mec_disp_atr_min * atr_ref and eff2 >= mec_disp_eff_min
                valid := true
                start_idx := 1
                
        if not valid
            float d_net3 = close - open[2]
            float d_tot3 = math.max(high, math.max(high[1], high[2])) - math.min(low, math.min(low[1], low[2]))
            float eff3 = d_tot3 > 0 ? (d_net3 / d_tot3) : 0
            if (b1 + b2 + b3) >= mec_disp_atr_min * atr_ref and eff3 >= mec_disp_eff_min
                valid := true
                start_idx := 2
                
    [valid, start_idx]

f_mec_get_impulse_sell(mss_lvl, atr_ref) =>
    int start_idx = 0
    bool valid = false
    
    if close < mss_lvl
        float b1 = math.max(0, open - close)
        float b2 = math.max(0, open[1] - close[1])
        float b3 = math.max(0, open[2] - close[2])
        
        float d_net1 = open - close
        float d_tot1 = high - low
        float eff1 = d_tot1 > 0 ? (d_net1 / d_tot1) : 0
        if b1 >= mec_disp_atr_min * atr_ref and eff1 >= mec_disp_eff_min
            valid := true
            start_idx := 0
            
        if not valid
            float d_net2 = open[1] - close
            float d_tot2 = math.max(high, high[1]) - math.min(low, low[1])
            float eff2 = d_tot2 > 0 ? (d_net2 / d_tot2) : 0
            if (b1 + b2) >= mec_disp_atr_min * atr_ref and eff2 >= mec_disp_eff_min
                valid := true
                start_idx := 1
                
        if not valid
            float d_net3 = open[2] - close
            float d_tot3 = math.max(high, math.max(high[1], high[2])) - math.min(low, math.min(low[1], low[2]))
            float eff3 = d_tot3 > 0 ? (d_net3 / d_tot3) : 0
            if (b1 + b2 + b3) >= mec_disp_atr_min * atr_ref and eff3 >= mec_disp_eff_min
                valid := true
                start_idx := 2
                
    [valid, start_idx]

f_mec_get_causal_ob_buy(impulse_start) =>
    int ob_start = -1
    int ob_end = -1
    bool found = false
    float top = na
    float bot = na
    for i = impulse_start + 1 to impulse_start + 10
        if close[i] < open[i]
            if not found
                ob_end := i
                ob_start := i
                found := true
            else
                ob_start := i
        else
            if found
                break
    if found
        top := high[ob_start]
        bot := low[ob_start]
        for i = ob_start to ob_end
            top := math.max(top, high[i])
            bot := math.min(bot, low[i])
    [found, top, bot]

f_mec_get_causal_ob_sell(impulse_start) =>
    int ob_start = -1
    int ob_end = -1
    bool found = false
    float top = na
    float bot = na
    for i = impulse_start + 1 to impulse_start + 10
        if close[i] > open[i]
            if not found
                ob_end := i
                ob_start := i
                found := true
            else
                ob_start := i
        else
            if found
                break
    if found
        top := high[ob_start]
        bot := low[ob_start]
        for i = ob_start to ob_end
            top := math.max(top, high[i])
            bot := math.min(bot, low[i])
    [found, top, bot]

f_mec_get_causal_fvg_buy(impulse_start, atr_ref) =>
    bool found = false
    float top = na
    float bot = na
    int bar = na
    for i = 0 to impulse_start
        if low[i] > high[i+2] and (low[i] - high[i+2]) >= atr_ref * 0.15
            found := true
            bot := high[i+2]
            top := low[i]
            bar := bar_index[i]
            break
    [found, top, bot, bar]

f_mec_get_causal_fvg_sell(impulse_start, atr_ref) =>
    bool found = false
    float top = na
    float bot = na
    int bar = na
    for i = 0 to impulse_start
        if high[i] < low[i+2] and (low[i+2] - high[i]) >= atr_ref * 0.15
            found := true
            top := low[i+2]
            bot := high[i]
            bar := bar_index[i]
            break
    [found, top, bot, bar]

// --- BUY ENGINE ---
if buy_mec_state != MEC_IDLE
    if h1_bull_consumed
        if buy_mec_state == MEC_SWEEPING
            mec_cnt_buy_rej_h1_sweep += 1
        else if buy_mec_state == MEC_SWEEP_CONF
            mec_cnt_buy_rej_h1_sweep_conf += 1
        else if buy_mec_state == MEC_MSS_CONF
            mec_cnt_buy_rej_h1_mss_conf += 1
            
        if buy_mec_state >= MEC_SWEEP_CONF
            if buy_has_crossed
                mec_cnt_buy_rej_after_cross += 1
            else
                mec_cnt_buy_rej_before_cross += 1
            if na(dbg_buy_exit_reason) or dbg_buy_exit_reason == "PENDING"
                dbg_buy_exit_reason := "H1 Consumed (" + (buy_mec_state == MEC_SWEEP_CONF ? "SWEEP" : "MSS") + ")"
                
        mec_cnt_buy_rej_h1 += 1
        buy_mec_state := MEC_IDLE
        
    else if buy_mec_state >= MEC_SWEEP_CONF and not na(buy_sweep_ext) and close < buy_sweep_ext
        if buy_mec_state == MEC_SWEEP_CONF
            mec_cnt_buy_rej_sl_sweep_conf += 1
        else if buy_mec_state == MEC_MSS_CONF
            mec_cnt_buy_rej_sl_mss_conf += 1
            
        if buy_has_crossed
            mec_cnt_buy_rej_after_cross += 1
        else
            mec_cnt_buy_rej_before_cross += 1
        if na(dbg_buy_exit_reason) or dbg_buy_exit_reason == "PENDING"
            dbg_buy_exit_reason := "SL Hit (" + (buy_mec_state == MEC_SWEEP_CONF ? "SWEEP" : "MSS") + ")"
            
        mec_cnt_buy_rej_sl += 1
        buy_mec_state := MEC_IDLE
        
    else if buy_mec_state == MEC_SWEEPING and (bar_index - buy_sweep_bar > mec_max_sweep_bars)
        mec_cnt_buy_rej_timeout += 1
        buy_mec_state := MEC_IDLE
        
    else if buy_mec_state == MEC_SWEEP_CONF and (bar_index - buy_sweep_bar > 18)
        mec_cnt_buy_rej_timeout += 1
        if buy_has_crossed
            mec_cnt_buy_rej_after_cross += 1
        else
            mec_cnt_buy_rej_before_cross += 1
        if na(dbg_buy_exit_reason) or dbg_buy_exit_reason == "PENDING"
            dbg_buy_exit_reason := "Timeout 18b (SWEEP_CONF)"
        buy_mec_state := MEC_IDLE

if buy_mec_state == MEC_IDLE
    if in_h1_bull_zone
        buy_mec_state := MEC_IN_POI
        mec_cnt_buy_poi += 1

if buy_mec_state == MEC_IN_POI
    if low < vis_last_pl
        buy_mec_state := MEC_SWEEPING
        buy_sweep_bar := bar_index
        buy_sweep_ext := low
        mec_cnt_buy_sweep += 1

if buy_mec_state == MEC_SWEEPING
    buy_sweep_ext := math.min(buy_sweep_ext, low)
    if close > vis_last_pl
        buy_mec_state := MEC_SWEEP_CONF
        buy_mss_target := current_mss_buy
        buy_has_crossed := false
        mec_cnt_buy_sweep_conf += 1
        if not na(buy_mss_target)
            mec_cnt_buy_sweep_conf_mss_ok += 1
            
        dbg_buy_sweep_time := time
        dbg_buy_mss_lvl := buy_mss_target
        dbg_buy_dist_atr := not na(buy_mss_target) ? (buy_mss_target - buy_sweep_ext) / atr_val[1] : na
        dbg_buy_max_reach := high
        dbg_buy_exit_reason := "PENDING"

if buy_mec_state == MEC_SWEEP_CONF
    dbg_buy_max_reach := math.max(dbg_buy_max_reach, high)
    if bar_confirmed and close > buy_mss_target
        if not buy_has_crossed
            buy_has_crossed := true
            mec_cnt_buy_mss_cross += 1
            
        [valid_imp, start_idx] = f_mec_get_impulse_buy(buy_mss_target, atr_val[1])
        if valid_imp
            mec_cnt_buy_mss_disp_ok += 1
            [found_ob, ob_t, ob_b] = f_mec_get_causal_ob_buy(start_idx)
            [found_fvg, fvg_t, fvg_b, fvg_bar] = f_mec_get_causal_fvg_buy(start_idx, atr_val[1])
            
            if found_ob and found_fvg
                buy_mec_state := MEC_MSS_CONF
                buy_ob_top := ob_t
                buy_ob_bot := ob_b
                buy_ob_mid := ob_b + (ob_t - ob_b) * 0.5
                buy_fvg_top := fvg_t
                buy_fvg_bot := fvg_b
                buy_fvg_bar := fvg_bar
                buy_impulse_top := high
                mec_cnt_buy_mss += 1
                dbg_buy_exit_reason := "SUCCESS (READY)"
            else
                mec_cnt_buy_rej_fvg_ob += 1
                mec_cnt_buy_rej_after_cross += 1
                dbg_buy_exit_reason := "Invalid OB/FVG"
                buy_mec_state := MEC_IDLE
        else
            mec_cnt_buy_mss_disp_ko += 1

if buy_mec_state == MEC_MSS_CONF
    if bar_index - buy_fvg_bar > 20
        buy_mec_state := MEC_IDLE
        mec_cnt_buy_rej_timeout += 1
    else if close < buy_fvg_bot
        buy_mec_state := MEC_IDLE
        mec_cnt_buy_rej_fvg_ob += 1
    else
        float dr_mid = buy_sweep_ext + (buy_impulse_top - buy_sweep_ext) * 0.5
        if low <= dr_mid
            buy_mec_state := MEC_READY
            mec_cnt_buy_ready += 1

// --- SELL ENGINE ---
if sell_mec_state != MEC_IDLE
    if h1_bear_consumed
        if sell_mec_state == MEC_SWEEPING
            mec_cnt_sell_rej_h1_sweep += 1
        else if sell_mec_state == MEC_SWEEP_CONF
            mec_cnt_sell_rej_h1_sweep_conf += 1
        else if sell_mec_state == MEC_MSS_CONF
            mec_cnt_sell_rej_h1_mss_conf += 1
            
        if sell_mec_state >= MEC_SWEEP_CONF
            if sell_has_crossed
                mec_cnt_sell_rej_after_cross += 1
            else
                mec_cnt_sell_rej_before_cross += 1
            if na(dbg_sell_exit_reason) or dbg_sell_exit_reason == "PENDING"
                dbg_sell_exit_reason := "H1 Consumed (" + (sell_mec_state == MEC_SWEEP_CONF ? "SWEEP" : "MSS") + ")"
                
        mec_cnt_sell_rej_h1 += 1
        sell_mec_state := MEC_IDLE
        
    else if sell_mec_state >= MEC_SWEEP_CONF and not na(sell_sweep_ext) and close > sell_sweep_ext
        if sell_mec_state == MEC_SWEEP_CONF
            mec_cnt_sell_rej_sl_sweep_conf += 1
        else if sell_mec_state == MEC_MSS_CONF
            mec_cnt_sell_rej_sl_mss_conf += 1
            
        if sell_has_crossed
            mec_cnt_sell_rej_after_cross += 1
        else
            mec_cnt_sell_rej_before_cross += 1
        if na(dbg_sell_exit_reason) or dbg_sell_exit_reason == "PENDING"
            dbg_sell_exit_reason := "SL Hit (" + (sell_mec_state == MEC_SWEEP_CONF ? "SWEEP" : "MSS") + ")"
            
        mec_cnt_sell_rej_sl += 1
        sell_mec_state := MEC_IDLE
        
    else if sell_mec_state == MEC_SWEEPING and (bar_index - sell_sweep_bar > mec_max_sweep_bars)
        mec_cnt_sell_rej_timeout += 1
        sell_mec_state := MEC_IDLE
        
    else if sell_mec_state == MEC_SWEEP_CONF and (bar_index - sell_sweep_bar > 18)
        mec_cnt_sell_rej_timeout += 1
        if sell_has_crossed
            mec_cnt_sell_rej_after_cross += 1
        else
            mec_cnt_sell_rej_before_cross += 1
        if na(dbg_sell_exit_reason) or dbg_sell_exit_reason == "PENDING"
            dbg_sell_exit_reason := "Timeout 18b (SWEEP_CONF)"
        sell_mec_state := MEC_IDLE

if sell_mec_state == MEC_IDLE
    if in_h1_bear_zone
        sell_mec_state := MEC_IN_POI
        mec_cnt_sell_poi += 1

if sell_mec_state == MEC_IN_POI
    if high > vis_last_ph
        sell_mec_state := MEC_SWEEPING
        sell_sweep_bar := bar_index
        sell_sweep_ext := high
        mec_cnt_sell_sweep += 1

if sell_mec_state == MEC_SWEEPING
    sell_sweep_ext := math.max(sell_sweep_ext, high)
    if close < vis_last_ph
        sell_mec_state := MEC_SWEEP_CONF
        sell_mss_target := current_mss_sell
        sell_has_crossed := false
        mec_cnt_sell_sweep_conf += 1
        if not na(sell_mss_target)
            mec_cnt_sell_sweep_conf_mss_ok += 1
            
        dbg_sell_sweep_time := time
        dbg_sell_mss_lvl := sell_mss_target
        dbg_sell_dist_atr := not na(sell_mss_target) ? (sell_sweep_ext - sell_mss_target) / atr_val[1] : na
        dbg_sell_max_reach := low
        dbg_sell_exit_reason := "PENDING"

if sell_mec_state == MEC_SWEEP_CONF
    dbg_sell_max_reach := math.min(dbg_sell_max_reach, low)
    if bar_confirmed and close < sell_mss_target
        if not sell_has_crossed
            sell_has_crossed := true
            mec_cnt_sell_mss_cross += 1
            
        [valid_imp, start_idx] = f_mec_get_impulse_sell(sell_mss_target, atr_val[1])
        if valid_imp
            mec_cnt_sell_mss_disp_ok += 1
            [found_ob, ob_t, ob_b] = f_mec_get_causal_ob_sell(start_idx)
            [found_fvg, fvg_t, fvg_b, fvg_bar] = f_mec_get_causal_fvg_sell(start_idx, atr_val[1])
            
            if found_ob and found_fvg
                sell_mec_state := MEC_MSS_CONF
                sell_ob_top := ob_t
                sell_ob_bot := ob_b
                sell_ob_mid := ob_b + (ob_t - ob_b) * 0.5
                sell_fvg_top := fvg_t
                sell_fvg_bot := fvg_b
                sell_fvg_bar := fvg_bar
                sell_impulse_bot := low
                mec_cnt_sell_mss += 1
                dbg_sell_exit_reason := "SUCCESS (READY)"
            else
                mec_cnt_sell_rej_fvg_ob += 1
                mec_cnt_sell_rej_after_cross += 1
                dbg_sell_exit_reason := "Invalid OB/FVG"
                sell_mec_state := MEC_IDLE
        else
            mec_cnt_sell_mss_disp_ko += 1

if sell_mec_state == MEC_MSS_CONF
    if bar_index - sell_fvg_bar > 20
        sell_mec_state := MEC_IDLE
        mec_cnt_sell_rej_timeout += 1
    else if close > sell_fvg_top
        sell_mec_state := MEC_IDLE
        mec_cnt_sell_rej_fvg_ob += 1
    else
        float dr_mid = sell_impulse_bot + (sell_sweep_ext - sell_impulse_bot) * 0.5
        if high >= dr_mid
            sell_mec_state := MEC_READY
            mec_cnt_sell_ready += 1

// ==========================================
// 5. DIAGNOSTICS MEC V1.0 + AUTOPSIE
// ==========================================
var table dbg_mec = table.new(position.bottom_right, 4, 30, border_color=color.gray, border_width=1, bgcolor=color.new(color.black, 15))
if barstate.islast
    table.cell(dbg_mec, 0, 0, "MEC V1.0 - BUY", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 0, "", bgcolor=color.new(color.black,15))
    table.cell(dbg_mec, 0, 1, "Entrées POI", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 1, str.tostring(mec_cnt_buy_poi), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 2, "Sweeps Démarrés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 2, str.tostring(mec_cnt_buy_sweep), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 3, "Sweeps Confirmés (MSS valid)", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 3, str.tostring(mec_cnt_buy_sweep_conf) + " (" + str.tostring(mec_cnt_buy_sweep_conf_mss_ok) + ")", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 0, 4, "--- FRANCHISSEMENT MSS ---", text_color=color.aqua, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 0, 5, "Clôtures au-delà MSS", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 5, str.tostring(mec_cnt_buy_mss_cross), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 6, "Impulsions OK (≥1.2A, ≥65%)", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 6, str.tostring(mec_cnt_buy_mss_disp_ok), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 7, "Impulsions Faibles (Rejetées)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 7, str.tostring(mec_cnt_buy_mss_disp_ko), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 0, 8, "--- ÉTATS DE REJETS ---", text_color=color.orange, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 0, 9, "Rejets AVANT franchissement MSS", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 9, str.tostring(mec_cnt_buy_rej_before_cross), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 10, "Rejets APRÈS franchissement MSS", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 10, str.tostring(mec_cnt_buy_rej_after_cross), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 0, 11, "SL hit dans SWEEP_CONF", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 11, str.tostring(mec_cnt_buy_rej_sl_sweep_conf), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 12, "H1 consommé dans SWEEP_CONF", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 12, str.tostring(mec_cnt_buy_rej_h1_sweep_conf), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 13, "H1 consommé dans SWEEPING", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 13, str.tostring(mec_cnt_buy_rej_h1_sweep), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 0, 14, "--- AUTOPSIE DERNIER SWEEP BUY ---", text_color=color.fuchsia, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 0, 15, "Date", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 15, not na(dbg_buy_sweep_time) ? str.format_time(dbg_buy_sweep_time, "dd/MM HH:mm", "America/New_York") : "-", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 16, "Niveau MSS 3/3", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 16, not na(dbg_buy_mss_lvl) ? str.tostring(dbg_buy_mss_lvl, format.mintick) : "na", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 17, "Distance MSS (ATR)", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 17, not na(dbg_buy_dist_atr) ? str.tostring(dbg_buy_dist_atr, "#.#") : "-", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 18, "Prix max atteint", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 18, not na(dbg_buy_max_reach) ? str.tostring(dbg_buy_max_reach, format.mintick) : "-", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 0, 19, "Cause de Sortie", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 1, 19, dbg_buy_exit_reason, text_color=color.yellow, text_size=size.small, text_halign=text.align_right)

    // SELL COLUMNS
    table.cell(dbg_mec, 2, 0, "MEC V1.0 - SELL", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 0, "", bgcolor=color.new(color.black,15))
    table.cell(dbg_mec, 2, 1, "Entrées POI", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 1, str.tostring(mec_cnt_sell_poi), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 2, "Sweeps Démarrés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 2, str.tostring(mec_cnt_sell_sweep), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 3, "Sweeps Confirmés (MSS valid)", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 3, str.tostring(mec_cnt_sell_sweep_conf) + " (" + str.tostring(mec_cnt_sell_sweep_conf_mss_ok) + ")", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 2, 4, "--- FRANCHISSEMENT MSS ---", text_color=color.aqua, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 2, 5, "Clôtures au-delà MSS", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 5, str.tostring(mec_cnt_sell_mss_cross), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 6, "Impulsions OK (≥1.2A, ≥65%)", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 6, str.tostring(mec_cnt_sell_mss_disp_ok), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 7, "Impulsions Faibles (Rejetées)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 7, str.tostring(mec_cnt_sell_mss_disp_ko), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 2, 8, "--- ÉTATS DE REJETS ---", text_color=color.orange, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 2, 9, "Rejets AVANT franchissement MSS", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 9, str.tostring(mec_cnt_sell_rej_before_cross), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 10, "Rejets APRÈS franchissement MSS", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 10, str.tostring(mec_cnt_sell_rej_after_cross), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 2, 11, "SL hit dans SWEEP_CONF", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 11, str.tostring(mec_cnt_sell_rej_sl_sweep_conf), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 12, "H1 consommé dans SWEEP_CONF", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 12, str.tostring(mec_cnt_sell_rej_h1_sweep_conf), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 13, "H1 consommé dans SWEEPING", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 13, str.tostring(mec_cnt_sell_rej_h1_sweep), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg_mec, 2, 14, "--- AUTOPSIE DERNIER SWEEP SELL ---", text_color=color.fuchsia, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 2, 15, "Date", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 15, not na(dbg_sell_sweep_time) ? str.format_time(dbg_sell_sweep_time, "dd/MM HH:mm", "America/New_York") : "-", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 16, "Niveau MSS 3/3", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 16, not na(dbg_sell_mss_lvl) ? str.tostring(dbg_sell_mss_lvl, format.mintick) : "na", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 17, "Distance MSS (ATR)", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 17, not na(dbg_sell_dist_atr) ? str.tostring(dbg_sell_dist_atr, "#.#") : "-", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 18, "Prix min atteint", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 18, not na(dbg_sell_max_reach) ? str.tostring(dbg_sell_max_reach, format.mintick) : "-", text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg_mec, 2, 19, "Cause de Sortie", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg_mec, 3, 19, dbg_sell_exit_reason, text_color=color.yellow, text_size=size.small, text_halign=text.align_right)
"""
    out_lines.append(instrumented_logic)
    with open('scanner_mtf_backtest_mec.pine', 'w', encoding='utf-8') as f:
        f.writelines(out_lines)

build_fixed_instrumentation()
