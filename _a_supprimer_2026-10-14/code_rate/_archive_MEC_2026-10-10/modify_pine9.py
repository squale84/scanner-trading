import re

def update_pine():
    with open("scanner_mtf_backtest_lab.pine", "r", encoding="utf-8") as f:
        content = f.read()

    old_sec = """h1_poi_bull_top = h1_data_obj.bull_top
h1_poi_bull_bot = h1_data_obj.bull_bot
h1_poi_bear_top = h1_data_obj.bear_top
h1_poi_bear_bot = h1_data_obj.bear_bot
h1_atr = h1_data_obj.atr
h1_ph = h1_data_obj.ph
h1_pl = h1_data_obj.pl
h1_cnt_buy_sweep = h1_data_obj.b_sweep
h1_cnt_buy_mss = h1_data_obj.b_mss
h1_cnt_buy_fvg = h1_data_obj.b_fvg
h1_cnt_buy_fvg_exp = h1_data_obj.b_fvg_exp
h1_cnt_buy_poi = h1_data_obj.b_poi
h1_cnt_buy_poi_rej = h1_data_obj.b_poi_rej
h1_cnt_sell_sweep = h1_data_obj.s_sweep
h1_cnt_sell_mss = h1_data_obj.s_mss
h1_cnt_sell_fvg = h1_data_obj.s_fvg
h1_cnt_sell_fvg_exp = h1_data_obj.s_fvg_exp
h1_cnt_sell_poi = h1_data_obj.s_poi
h1_cnt_sell_poi_rej = h1_data_obj.s_poi_rej"""

    new_sec = """h1_poi_bull_top = na(h1_data_obj) ? na : h1_data_obj.bull_top
h1_poi_bull_bot = na(h1_data_obj) ? na : h1_data_obj.bull_bot
h1_poi_bear_top = na(h1_data_obj) ? na : h1_data_obj.bear_top
h1_poi_bear_bot = na(h1_data_obj) ? na : h1_data_obj.bear_bot
h1_atr = na(h1_data_obj) ? na : h1_data_obj.atr
h1_ph = na(h1_data_obj) ? na : h1_data_obj.ph
h1_pl = na(h1_data_obj) ? na : h1_data_obj.pl
h1_cnt_buy_sweep = na(h1_data_obj) ? 0 : h1_data_obj.b_sweep
h1_cnt_buy_mss = na(h1_data_obj) ? 0 : h1_data_obj.b_mss
h1_cnt_buy_fvg = na(h1_data_obj) ? 0 : h1_data_obj.b_fvg
h1_cnt_buy_fvg_exp = na(h1_data_obj) ? 0 : h1_data_obj.b_fvg_exp
h1_cnt_buy_poi = na(h1_data_obj) ? 0 : h1_data_obj.b_poi
h1_cnt_buy_poi_rej = na(h1_data_obj) ? 0 : h1_data_obj.b_poi_rej
h1_cnt_sell_sweep = na(h1_data_obj) ? 0 : h1_data_obj.s_sweep
h1_cnt_sell_mss = na(h1_data_obj) ? 0 : h1_data_obj.s_mss
h1_cnt_sell_fvg = na(h1_data_obj) ? 0 : h1_data_obj.s_fvg
h1_cnt_sell_fvg_exp = na(h1_data_obj) ? 0 : h1_data_obj.s_fvg_exp
h1_cnt_sell_poi = na(h1_data_obj) ? 0 : h1_data_obj.s_poi
h1_cnt_sell_poi_rej = na(h1_data_obj) ? 0 : h1_data_obj.s_poi_rej"""

    content = content.replace(old_sec, new_sec)

    with open("scanner_mtf_backtest_lab.pine", "w", encoding="utf-8") as f:
        f.write(content)

update_pine()
