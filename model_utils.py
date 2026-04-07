"""
model_utils.py — Prediction & Suggestion Engine
Based on Group 10 Capstone: CatBoost model (R²=0.9243)
Key finding: BO ratio is the #1 predictor (Pearson r = +0.87)

CALCULATION APPROACH:
- Current rate comes from REAL dataset (delivery_offices / total_offices)
- Suggestions calculated using: each BO added delivers at 98.7% rate
  new_rate = (delivery_offices + 0.987 * added_bo) / (total + added_bo)
- PO activation: each activated PO adds 1 delivery office to count
"""

import pandas as pd
import math


# ── Performance Tiers (from K-Means clustering of 720 districts) ─────────────
TIERS = {
    "high": {
        "label":       "High Performance",
        "emoji":       "🟢",
        "color":       "#22c55e",
        "bg":          "#052010",
        "border":      "#22c55e50",
        "min_rate":    0.95,
        "description": "Excellent! This district is among the top performers in India.",
        "avg_bo_ratio": 0.905,
    },
    "good": {
        "label":       "Good Performance",
        "emoji":       "🔵",
        "color":       "#3b82f6",
        "bg":          "#030d1e",
        "border":      "#3b82f650",
        "min_rate":    0.85,
        "description": "Above average. Small improvements can push this into the top tier.",
        "avg_bo_ratio": 0.861,
    },
    "moderate": {
        "label":       "Moderate Performance",
        "emoji":       "🟡",
        "color":       "#eab308",
        "bg":          "#0c0a00",
        "border":      "#eab30850",
        "min_rate":    0.70,
        "description": "Below national average. Targeted action can make a big difference.",
        "avg_bo_ratio": 0.830,
    },
    "low": {
        "label":       "Low Performance",
        "emoji":       "🔴",
        "color":       "#ef4444",
        "bg":          "#120404",
        "border":      "#ef444450",
        "min_rate":    0.0,
        "description": "Needs urgent attention. Infrastructure restructuring is recommended.",
        "avg_bo_ratio": 0.159,
    },
}


def get_tier(rate: float) -> dict:
    if rate >= 0.95:   return TIERS["high"]
    elif rate >= 0.85: return TIERS["good"]
    elif rate >= 0.70: return TIERS["moderate"]
    else:              return TIERS["low"]


def get_next_tier(current_tier: dict):
    order   = ["low", "moderate", "good", "high"]
    cur_key = next(k for k, v in TIERS.items() if v["label"] == current_tier["label"])
    cur_idx = order.index(cur_key)
    if cur_idx < len(order) - 1:
        return TIERS[order[cur_idx + 1]]
    return None


def calculate_suggestion(bo: int, po: int, ho: int,
                          current_rate: float) -> dict:
    """
    Calculate how many Branch Offices to add to reach the next performance tier.

    Uses real-world logic:
      new_rate = (delivery_offices + 0.987 * added_bo) / (total_offices + added_bo)

    Each BO added:
      - Increases total offices by 1
      - Increases delivery offices by ~0.987 (98.7% BO delivery rate)
    """
    total         = bo + po + ho
    delivery_off  = round(current_rate * total)   # estimated delivery offices
    current_tier  = get_tier(current_rate)
    next_tier     = get_next_tier(current_tier)
    inactive_pos  = max(0, int(po * 0.238))        # ~23.8% POs are non-delivering

    base = {
        "already_top":      next_tier is None,
        "current_tier":     current_tier,
        "next_tier":        next_tier,
        "bo_to_add":        0,
        "po_to_activate":   inactive_pos,
        "new_bo":           bo,
        "expected_rate":    current_rate,
        "improvement":      0.0,
        "new_tier":         current_tier,
        "bo_ratio_current": round(bo / total, 4) if total > 0 else 0,
        "bo_ratio_after":   round(bo / total, 4) if total > 0 else 0,
        "action_summary":   "",
    }

    if next_tier is None:
        base["action_summary"] = (
            "This district is already in the top performance tier. "
            "Focus on maintaining infrastructure quality."
        )
        return base

    # Target: just above next tier threshold
    target_rate = next_tier["min_rate"] + 0.005

    # --- Find BOs to add ---
    bo_to_add = 0
    new_rate  = current_rate
    for x in range(0, 5001):
        nt = total + x
        nd = delivery_off + int(0.987 * x)
        nr = nd / nt
        if nr >= target_rate:
            bo_to_add = x
            new_rate  = round(nr, 4)
            break
    else:
        bo_to_add = 5000
        nt        = total + bo_to_add
        new_rate  = round((delivery_off + int(0.987 * bo_to_add)) / nt, 4)

    improvement = round((new_rate - current_rate) * 100, 2)

    base.update({
        "bo_to_add":      bo_to_add,
        "new_bo":         bo + bo_to_add,
        "expected_rate":  new_rate,
        "improvement":    improvement,
        "new_tier":       get_tier(new_rate),
        "bo_ratio_after": round((bo + bo_to_add) / (total + bo_to_add), 4),
        "action_summary": (
            f"Add {bo_to_add} Branch Offices → delivery rate rises from "
            f"{current_rate*100:.1f}% to {new_rate*100:.1f}% "
            f"(+{improvement:.1f} percentage points)"
        ),
    })
    return base


def explain_office_types() -> dict:
    return {
        "BO": {
            "full_name":    "Branch Post Office",
            "icon":         "🟩",
            "delivery_pct": 98.7,
            "description": (
                "The backbone of rural postal delivery. "
                "Branch Offices are small local post offices found in villages and "
                "small towns. Nearly all of them (98.7%) actively deliver mail to homes — "
                "making them the most important type for delivery performance."
            ),
            "why_important": "More BOs = higher delivery rate (strongest predictor)",
        },
        "PO": {
            "full_name":    "Sub Post Office",
            "icon":         "🟧",
            "delivery_pct": 76.2,
            "description": (
                "Medium-sized post offices found at the town or tehsil level. "
                "They offer banking, insurance, and postal services. "
                "However, nearly 1 in 4 Sub Post Offices (23.8%) has NO active delivery — "
                "meaning mail piles up but doesn't reach homes."
            ),
            "why_important": "Many inactive POs drag down the district delivery rate",
        },
        "HO": {
            "full_name":    "Head Post Office",
            "icon":         "🟦",
            "delivery_pct": 99.1,
            "description": (
                "The main administrative post office of a district. "
                "Head Post Offices handle high-volume processing, Speed Post, "
                "and government mail. Almost all (99.1%) actively deliver. "
                "However, there is usually only 1–3 per district."
            ),
            "why_important": "Very reliable but few in number — limited overall impact",
        },
    }


def load_district_data(csv_path: str = "district_aggregated.csv") -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df['statename'] = df['statename'].str.strip().str.upper()
    df['district']  = df['district'].str.strip().str.upper()
    return df


def get_states(df: pd.DataFrame) -> list:
    return sorted(df['statename'].unique().tolist())


def get_districts(df: pd.DataFrame, state: str) -> list:
    return sorted(df[df['statename'] == state.upper()]['district'].unique().tolist())


def get_district_info(df: pd.DataFrame, state: str, district: str):
    row = df[
        (df['statename'] == state.upper()) &
        (df['district']  == district.upper())
    ]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "statename":              r['statename'],
        "district":               r['district'],
        "bo_count":               int(r['bo_count']),
        "po_count":               int(r['po_count']),
        "ho_count":               int(r['ho_count']),
        "total_offices":          int(r['total_offices']),
        "delivery_offices":       int(r['delivery_offices']),
        "district_delivery_rate": float(r['district_delivery_rate']),
        "bo_ratio":               float(r['bo_ratio']),
    }
