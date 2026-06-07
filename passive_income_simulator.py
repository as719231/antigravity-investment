# --- 被動收入模擬設定 ---
MONTHLY_INVESTMENT = 5000       # 每月投入金額 (台幣)
ANNUAL_DIVIDEND_YIELD = 0.05    # 預期年化股息率 (5% 是 00878 的保守估計)
ANNUAL_GROWTH_RATE = 0.03       # 預期股價年均成長率 (3% 是大盤長期保守估計)
YEARS = 15                      # 模擬年數

def simulate_investment():
    # 初始數據
    total_assets = 0
    total_invested = 0
    monthly_passive_income = 0
    
    # 確保 Windows 主控台編碼相容性
    print("\n--- [抗重力計畫] 被動收入增長模擬 (每月投入 {:,} 元) ---".format(MONTHLY_INVESTMENT))
    print("-" * 65)
    print("{:<6} | {:<12} | {:<12} | {:<12}".format("年份", "總投入金額", "總資產價值", "月領被動收入"))
    print("-" * 65)
    
    for year in range(1, YEARS + 1):
        for month in range(12):
            total_invested += MONTHLY_INVESTMENT
            total_assets += MONTHLY_INVESTMENT
            total_assets *= (1 + ANNUAL_GROWTH_RATE) ** (1/12)
            
        dividends = total_assets * ANNUAL_DIVIDEND_YIELD
        total_assets += dividends
        monthly_passive_income = (total_assets * ANNUAL_DIVIDEND_YIELD) / 12
        
        if year % 3 == 0 or year == 1:
            print("{:<8} | {:>12,.0f} | {:>12,.0f} | {:>14,.0f} 元".format(year, total_invested, total_assets, monthly_passive_income))
    
    print("-" * 65)
    print("結論：堅持 {} 年後，您的「被動收入」相當於每月加薪 {:,} 元！".format(YEARS, int(monthly_passive_income)))
    print("這還不包含如果您薪水增加時，多投入所帶來的複利效應。")
    print("-" * 65)

if __name__ == "__main__":
    simulate_investment()
