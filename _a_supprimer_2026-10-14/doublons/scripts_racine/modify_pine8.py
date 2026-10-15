import re

def update_pine():
    with open("scanner_mtf_backtest_lab.pine", "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Define the UDT at the top of the file, right after imports/version (let's say around line 100)
    udt_definition = """
type H1Data
    float bull_top
    float bull_bot
    float bear_top
    float bear_bot
    float atr
    float ph
    float pl
    int b_sweep
    int b_mss
    int b_fvg
    int b_fvg_exp
    int b_poi
    int b_poi_rej
    int s_sweep
    int s_mss
    int s_fvg
    int s_fvg_exp
    int s_poi
    int s_poi_rej

"""
    # Insert right before f_get_h1_data()
    content = content.replace("f_get_h1_data() =>", udt_definition + "f_get_h1_data() =>")

    # 2. Fix the return inside f_get_h1_data
    # The old return was:
    #     [h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr[1], h1_ph[1], h1_pl[1], h1_cnt_buy_sweep, h1_cnt_buy_mss, h1_cnt_buy_fvg, h1_cnt_buy_fvg_exp, h1_cnt_buy_poi, h1_cnt_buy_poi_rej, h1_cnt_sell_sweep, h1_cnt_sell_mss, h1_cnt_sell_fvg, h1_cnt_sell_fvg_exp, h1_cnt_sell_poi, h1_cnt_sell_poi_rej]
    
    old_return = r"    \[h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr\[1\], h1_ph\[1\], h1_pl\[1\], h1_cnt_buy_sweep, h1_cnt_buy_mss, h1_cnt_buy_fvg, h1_cnt_buy_fvg_exp, h1_cnt_buy_poi, h1_cnt_buy_poi_rej, h1_cnt_sell_sweep, h1_cnt_sell_mss, h1_cnt_sell_fvg, h1_cnt_sell_fvg_exp, h1_cnt_sell_poi, h1_cnt_sell_poi_rej\]"
    new_return = "    H1Data.new(h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr[1], h1_ph[1], h1_pl[1], h1_cnt_buy_sweep, h1_cnt_buy_mss, h1_cnt_buy_fvg, h1_cnt_buy_fvg_exp, h1_cnt_buy_poi, h1_cnt_buy_poi_rej, h1_cnt_sell_sweep, h1_cnt_sell_mss, h1_cnt_sell_fvg, h1_cnt_sell_fvg_exp, h1_cnt_sell_poi, h1_cnt_sell_poi_rej)"
    content = re.sub(old_return, new_return, content)

    # 3. Fix the request.security call and unpacking
    old_sec = r"\[h1_poi_bull_top, h1_poi_bull_bot, h1_poi_bear_top, h1_poi_bear_bot, h1_atr, h1_ph, h1_pl, h1_cnt_buy_sweep, h1_cnt_buy_mss, h1_cnt_buy_fvg, h1_cnt_buy_fvg_exp, h1_cnt_buy_poi, h1_cnt_buy_poi_rej, h1_cnt_sell_sweep, h1_cnt_sell_mss, h1_cnt_sell_fvg, h1_cnt_sell_fvg_exp, h1_cnt_sell_poi, h1_cnt_sell_poi_rej\] = request\.security\(syminfo\.tickerid, \"60\", f_get_h1_data\(\), barmerge\.gaps_off, barmerge\.lookahead_off\)"
    new_sec = """h1_data_obj = request.security(syminfo.tickerid, "60", f_get_h1_data(), barmerge.gaps_off, barmerge.lookahead_off)
h1_poi_bull_top = h1_data_obj.bull_top
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
    content = re.sub(old_sec, new_sec, content)

    with open("scanner_mtf_backtest_lab.pine", "w", encoding="utf-8") as f:
        f.write(content)

update_pine()
