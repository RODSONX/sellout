import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime

# Add current dir to path
sys.path.append(os.getcwd())
import engines.forecast as forecast

def test_v110_logic():
    print("--- Starting v1.10 Global Period Logic Test ---")
    
    # 1. Product A: Jan(10), Feb(20)
    # 2. Product B: Jan(15) only
    
    # Simulating helpers.py logic:
    # df_sell_current should have Product A (20) and Product B (0)
    df_sell_current = pd.DataFrame([
        {"cliente": "L1", "produto": "A", "segmento": "S1", "venda": 20, "estoque": 5},
        {"cliente": "L1", "produto": "B", "segmento": "S1", "venda": 0, "estoque": 0}
    ])
    
    # df_hist should have Product A (Jan 10) and Product B (Jan 15)
    df_hist = pd.DataFrame([
        {"cliente": "L1", "produto": "A", "mes": "2026-01", "venda": 10},
        {"cliente": "L1", "produto": "B", "mes": "2026-01", "venda": 15}
    ])
    
    calendar = {m: "verão" for m in range(1, 13)}
    seasonality = {"s1": {"verão": 1.0}}
    
    results = forecast.run_forecast_engine(
        df_sell_current, df_hist, calendar, seasonality,
        current_month=2, lead_time_days=0
    )
    
    print("\nResults:")
    print(results[["produto", "venda", "media_vendas", "tendencia", "demanda_prevista"]])
    
    # Assertions
    res_a = results[results["produto"] == "A"].iloc[0]
    res_b = results[results["produto"] == "B"].iloc[0]
    
    # Product A: Current=20, Hist=10 -> Avg=10. Trend for [10, 20] -> CP = 2.0 (clip 1.5). Stability 0.5. final ~1.3
    assert res_a["venda"] == 20
    assert res_a["media_vendas"] == 10, f"A avg should be 10 (history only), got {res_a['media_vendas']}"
    
    # Product B: Current=0, Hist=15 -> Avg=15. Trend for [15, 0] -> CP = 0 (clip 0.6). Med = 0 (clip 0.6). Stability 0. Final 0.6
    assert res_b["venda"] == 0
    assert res_b["media_vendas"] == 15, f"B avg should be 15 (history only), got {res_b['media_vendas']}"
    assert res_b["tendencia"] == 0.6, f"B trend should be 0.6 (min clip), got {res_b['tendencia']}"

    print("\n--- v1.10 Logic Passed! ---")

if __name__ == "__main__":
    test_v110_logic()
