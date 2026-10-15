import re

def update_pine():
    with open("scanner_mtf_backtest_lab.pine", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. H1 Counters Declaration
    h1_counters = """
    var int h1_cnt_buy_sweep = 0
    var int h1_cnt_buy_mss = 0
    var int h1_cnt_buy_fvg = 0
    var int h1_cnt_buy_fvg_exp = 0
    var int h1_cnt_buy_poi = 0
    var int h1_cnt_buy_poi_rej = 0
    
    var int h1_cnt_sell_sweep = 0
    var int h1_cnt_sell_mss = 0
    var int h1_cnt_sell_fvg = 0
    var int h1_cnt_sell_fvg_exp = 0
    var int h1_cnt_sell_poi = 0
    var int h1_cnt_sell_poi_rej = 0
"""
    content = content.replace("var int buy_mss_bar = na", h1_counters + "\n    var int buy_mss_bar = na")

    # 2. H1 Counters Increment (BUY)
    content = content.replace("buy_sweep_low := low", "buy_sweep_low := low\n            h1_cnt_buy_sweep += 1")
    content = content.replace("buy_mss_bar := bar_index", "buy_mss_bar := bar_index\n            h1_cnt_buy_mss += 1")
    content = content.replace("buy_state := 3", "buy_state := 3\n            h1_cnt_buy_fvg += 1")
    content = content.replace("buy_state := 0 // Expiration FVG causale H1 (3 bougies)", "buy_state := 0\n            h1_cnt_buy_fvg_exp += 1 // Expiration FVG causale H1 (3 bougies)")
    
    content = content.replace("""            if poi_top >= poi_bot
                buy_poi_top := poi_top
                buy_poi_bot := poi_bot
                buy_state := 4
            else
                buy_state := 0
        else
            buy_state := 0""", """            if poi_top >= poi_bot
                buy_poi_top := poi_top
                buy_poi_bot := poi_bot
                buy_state := 4
                h1_cnt_buy_poi += 1
            else
                buy_state := 0
                h1_cnt_buy_poi_rej += 1
        else
            buy_state := 0
            h1_cnt_buy_poi_rej += 1""")

    # 3. H1 Counters Increment (SELL)
    content = content.replace("sell_sweep_high := high", "sell_sweep_high := high\n            h1_cnt_sell_sweep += 1")
    content = content.replace("sell_mss_bar := bar_index", "sell_mss_bar := bar_index\n            h1_cnt_sell_mss += 1")
    content = content.replace("sell_state := 3", "sell_state := 3\n            h1_cnt_sell_fvg += 1")
    content = content.replace("sell_state := 0 // Expiration FVG causale H1 (3 bougies)", "sell_state := 0\n            h1_cnt_sell_fvg_exp += 1 // Expiration FVG causale H1 (3 bougies)")
    
    content = content.replace("""            if poi_top >= poi_bot
                sell_poi_top := poi_top
                sell_poi_bot := poi_bot
                sell_state := 4
            else
                sell_state := 0
        else
            sell_state := 0""", """            if poi_top >= poi_bot
                sell_poi_top := poi_top
                sell_poi_bot := poi_bot
                sell_state := 4
                h1_cnt_sell_poi += 1
            else
                sell_state := 0
                h1_cnt_sell_poi_rej += 1
        else
            sell_state := 0
            h1_cnt_sell_poi_rej += 1""")

    # 4. H1 Return variables
    old_h1_return = "    [h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr[1], h1_ph[1], h1_pl[1]]"
    new_h1_return = "    [h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr[1], h1_ph[1], h1_pl[1], h1_cnt_buy_sweep, h1_cnt_buy_mss, h1_cnt_buy_fvg, h1_cnt_buy_fvg_exp, h1_cnt_buy_poi, h1_cnt_buy_poi_rej, h1_cnt_sell_sweep, h1_cnt_sell_mss, h1_cnt_sell_fvg, h1_cnt_sell_fvg_exp, h1_cnt_sell_poi, h1_cnt_sell_poi_rej]"
    content = content.replace(old_h1_return, new_h1_return)

    old_sec_call = '[h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr, h1_ph, h1_pl] = request.security(syminfo.tickerid, "60", f_get_h1_data(), barmerge.gaps_off, barmerge.lookahead_off)'
    new_sec_call = '[h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr, h1_ph, h1_pl, h1_cnt_buy_sweep, h1_cnt_buy_mss, h1_cnt_buy_fvg, h1_cnt_buy_fvg_exp, h1_cnt_buy_poi, h1_cnt_buy_poi_rej, h1_cnt_sell_sweep, h1_cnt_sell_mss, h1_cnt_sell_fvg, h1_cnt_sell_fvg_exp, h1_cnt_sell_poi, h1_cnt_sell_poi_rej] = request.security(syminfo.tickerid, "60", f_get_h1_data(), barmerge.gaps_off, barmerge.lookahead_off)'
    content = content.replace(old_sec_call, new_sec_call)

    # 5. M5 Counters Declaration
    m5_counters = """
var int cnt_buy_in_poi = 0
var int cnt_sell_in_poi = 0
var int cnt_buy_ob_rej = 0
var int cnt_sell_ob_rej = 0
var int cnt_buy_limit_sent = 0
var int cnt_sell_limit_sent = 0
var int cnt_buy_limit_filled = 0
var int cnt_sell_limit_filled = 0
var int cnt_buy_limit_cancel = 0
var int cnt_sell_limit_cancel = 0
"""
    content = content.replace("var int cnt_sweep_l    = 0", m5_counters + "var int cnt_sweep_l    = 0")

    # 6. M5 Counters Increment (BUY)
    content = content.replace("buy_state := STATE_IN_POI", "buy_state := STATE_IN_POI\n        cnt_buy_in_poi += 1")
    # Need to only replace the first occurrence for BUY which is in the BUY transition block.
    
    content = content.replace("""    if not na(h1_bull_zone_top) and buy_ob_mid <= h1_bull_zone_top and buy_ob_mid >= h1_bull_zone_bot
        buy_state := STATE_READY
        cnt_buy_ready += 1
    else
        buy_state := STATE_IDLE""", """    if not na(h1_bull_zone_top) and buy_ob_mid <= h1_bull_zone_top and buy_ob_mid >= h1_bull_zone_bot
        buy_state := STATE_READY
        cnt_buy_ready += 1
    else
        buy_state := STATE_IDLE
        cnt_buy_ob_rej += 1""")

    content = content.replace("""    if strategy.opentrades > 0 and strategy.position_size > 0
        buy_state := STATE_IDLE
        in_pos := true""", """    if strategy.opentrades > 0 and strategy.position_size > 0
        buy_state := STATE_IDLE
        in_pos := true
        cnt_buy_limit_filled += 1""")

    content = content.replace("""        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
        buy_state := STATE_IDLE""", """        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE""")
        
    content = content.replace("""        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
        buy_state := STATE_IDLE""", """        if buy_state == STATE_PENDING_LIMIT
            strategy.cancel("Long")
            cnt_buy_limit_cancel += 1
        buy_state := STATE_IDLE""") # run twice? the previous replace will change both occurrences since it matches exactly. Wait, the replace string is the same. Yes, it changes all matching instances.

    # 7. M5 Counters Increment (SELL)
    content = content.replace("sell_state := STATE_IN_POI", "sell_state := STATE_IN_POI\n        cnt_sell_in_poi += 1")

    content = content.replace("""    if not na(h1_bear_zone_bot) and sell_ob_mid <= h1_bear_zone_top and sell_ob_mid >= h1_bear_zone_bot
        sell_state := STATE_READY
        cnt_sell_ready += 1
    else
        sell_state := STATE_IDLE""", """    if not na(h1_bear_zone_bot) and sell_ob_mid <= h1_bear_zone_top and sell_ob_mid >= h1_bear_zone_bot
        sell_state := STATE_READY
        cnt_sell_ready += 1
    else
        sell_state := STATE_IDLE
        cnt_sell_ob_rej += 1""")

    content = content.replace("""    if strategy.opentrades > 0 and strategy.position_size < 0
        sell_state := STATE_IDLE
        in_pos := true""", """    if strategy.opentrades > 0 and strategy.position_size < 0
        sell_state := STATE_IDLE
        in_pos := true
        cnt_sell_limit_filled += 1""")

    content = content.replace("""        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
        sell_state := STATE_IDLE""", """        if sell_state == STATE_PENDING_LIMIT
            strategy.cancel("Short")
            cnt_sell_limit_cancel += 1
        sell_state := STATE_IDLE""")

    # 8. M5 Limit Sent increment
    content = content.replace('strategy.entry("Long", strategy.long, qty=qty, limit=b_entry, comment=lab_tag)', 'strategy.entry("Long", strategy.long, qty=qty, limit=b_entry, comment=lab_tag)\n                cnt_buy_limit_sent += 1')
    content = content.replace('strategy.entry("Short", strategy.short, qty=qty, limit=s_entry, comment=lab_tag)', 'strategy.entry("Short", strategy.short, qty=qty, limit=s_entry, comment=lab_tag)\n                cnt_sell_limit_sent += 1')

    # 9. Update the debug table
    table_logic = """
// ==========================================
// 6. TABLEAU DE DIAGNOSTIC (DEBUG) — funnel de la séquence causale sur toute la période testée.
// Purement informatif, à retirer une fois le diagnostic terminé.
// ==========================================
var table dbg = table.new(position.bottom_right, 4, 30, border_color=color.gray, border_width=1, bgcolor=color.new(color.black, 15))
if barstate.islast
    // COLONNE 1: BUY
    table.cell(dbg, 0, 0, "DIAGNOSTIC BUY", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 0, "", bgcolor=color.new(color.black,15))
    table.cell(dbg, 0, 1, "H1 Sweeps détectés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 1, str.tostring(h1_cnt_buy_sweep), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 2, "H1 MSS confirmés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 2, str.tostring(h1_cnt_buy_mss), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 3, "H1 FVG validées", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 3, str.tostring(h1_cnt_buy_fvg), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 4, "H1 FVG expirées", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 4, str.tostring(h1_cnt_buy_fvg_exp), text_color=color.gray, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 5, "H1 POI Validés (Discount)", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 5, str.tostring(h1_cnt_buy_poi), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 6, "H1 POI Rejetés (Eq)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 6, str.tostring(h1_cnt_buy_poi_rej), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg, 0, 7, "---", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    
    table.cell(dbg, 0, 8, "M5 Entrées dans POI", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 8, str.tostring(cnt_buy_in_poi), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 9, "M5 Sweeps", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 9, str.tostring(cnt_sweep_l), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 10, "M5 MSS confirmés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 10, str.tostring(cnt_buy_mss), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 11, "M5 FVG causales", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 11, str.tostring(cnt_buy_fvg), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 12, "M5 OB Rejetés (hors POI)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 12, str.tostring(cnt_buy_ob_rej), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 13, "M5 READY / Limit préparé", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 13, str.tostring(cnt_buy_ready), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 14, "M5 Abandon : SL hors ATR", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 14, str.tostring(cnt_buy_sl_invalid), text_color=color.gray, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 15, "M5 Abandon : pas de cible", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 15, str.tostring(cnt_buy_no_target), text_color=color.gray, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg, 0, 16, "M5 Limit Envoyés", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 16, str.tostring(cnt_buy_limit_sent), text_color=color.yellow, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 17, "M5 Limit Exécutés", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 17, str.tostring(cnt_buy_limit_filled), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 18, "M5 Limit Annulés (contexte)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 18, str.tostring(cnt_buy_limit_cancel), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 0, 19, "M5 Limit Expirés (12 barres)", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 1, 19, str.tostring(cnt_buy_expired_limit), text_color=color.gray, text_size=size.small, text_halign=text.align_right)

    // COLONNE 2: SELL
    table.cell(dbg, 2, 0, "DIAGNOSTIC SELL", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 0, "", bgcolor=color.new(color.black,15))
    table.cell(dbg, 2, 1, "H1 Sweeps détectés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 1, str.tostring(h1_cnt_sell_sweep), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 2, "H1 MSS confirmés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 2, str.tostring(h1_cnt_sell_mss), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 3, "H1 FVG validées", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 3, str.tostring(h1_cnt_sell_fvg), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 4, "H1 FVG expirées", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 4, str.tostring(h1_cnt_sell_fvg_exp), text_color=color.gray, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 5, "H1 POI Validés (Premium)", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 5, str.tostring(h1_cnt_sell_poi), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 6, "H1 POI Rejetés (Eq)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 6, str.tostring(h1_cnt_sell_poi_rej), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg, 2, 7, "---", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    
    table.cell(dbg, 2, 8, "M5 Entrées dans POI", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 8, str.tostring(cnt_sell_in_poi), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 9, "M5 Sweeps", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 9, str.tostring(cnt_sweep_h), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 10, "M5 MSS confirmés", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 10, str.tostring(cnt_sell_mss), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 11, "M5 FVG causales", text_color=color.white, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 11, str.tostring(cnt_sell_fvg), text_color=color.white, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 12, "M5 OB Rejetés (hors POI)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 12, str.tostring(cnt_sell_ob_rej), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 13, "M5 READY / Limit préparé", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 13, str.tostring(cnt_sell_ready), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 14, "M5 Abandon : SL hors ATR", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 14, str.tostring(cnt_sell_sl_invalid), text_color=color.gray, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 15, "M5 Abandon : pas de cible", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 15, str.tostring(cnt_sell_no_target), text_color=color.gray, text_size=size.small, text_halign=text.align_right)
    
    table.cell(dbg, 2, 16, "M5 Limit Envoyés", text_color=color.yellow, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 16, str.tostring(cnt_sell_limit_sent), text_color=color.yellow, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 17, "M5 Limit Exécutés", text_color=color.lime, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 17, str.tostring(cnt_sell_limit_filled), text_color=color.lime, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 18, "M5 Limit Annulés (contexte)", text_color=color.red, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 18, str.tostring(cnt_sell_limit_cancel), text_color=color.red, text_size=size.small, text_halign=text.align_right)
    table.cell(dbg, 2, 19, "M5 Limit Expirés (12 barres)", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
    table.cell(dbg, 3, 19, str.tostring(cnt_sell_expired_limit), text_color=color.gray, text_size=size.small, text_halign=text.align_right)
"""
    # Replace the old debug table block. We find it using a regex.
    table_pattern = re.compile(r'// ==========================================\n// 6\. TABLEAU DE DIAGNOSTIC \(DEBUG\) — funnel de la séquence causale.*?(?=if h1_bull_consumed and not na\(h1_bull_box\))', re.DOTALL)
    
    content = table_pattern.sub(table_logic + "\n", content)

    with open("scanner_mtf_backtest_lab.pine", "w", encoding="utf-8") as f:
        f.write(content)

update_pine()
