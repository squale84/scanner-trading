def fix_pine():
    with open("scanner_mtf_backtest_lab.pine", "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    with open("scanner_mtf_backtest_lab.pine", "w", encoding="utf-8") as f:
        for i, line in enumerate(lines):
            # The accidental insertions are on lines > 500 (inside the M5 section)
            if "h1_cnt_buy_sweep +=" in line and i > 500:
                continue
            if "h1_cnt_sell_sweep +=" in line and i > 500:
                continue
            
            f.write(line)

fix_pine()
