# =============================================================
# RYVA Project — cognitive_engine/cls_engine.py
# Purpose : Rule-based Cognitive Load Score (CLS) engine
#           Pure Python maths — no AI yet
# Author  : RYVA Team
# Usage   : python cognitive_engine/cls_engine.py
# Done When:
#   compute_cls(ear=0.17, head_pitch=22, blink_rate=26,
#               movement_var=70, temp=36, baseline=defaults)
#   → returns above 60
#   Healthy values → returns below 35
# =============================================================

# ==============================================================
# DEFAULT BASELINE
# This is the "healthy normal" for an average operator.
# Later, Step 2 (calibration) will replace this with the
# operator's personal baseline measured in the first 3 minutes.
# ==============================================================

DEFAULT_BASELINE = {
    "ear"      : 0.30,   # Normal eye openness (open eyes ~0.28–0.32)
    "move_max" : 50.0,   # Maximum normal movement variance
}


# ==============================================================
# CLS SCORE BANDS
# ==============================================================

CLS_GREEN = (0,  40)    # Safe — normal operation
CLS_AMBER = (40, 70)    # Warning — RYVA adapts the interface
CLS_RED   = (70, 100)   # Critical — RYVA intervenes


def get_cls_band(score):
    """
    Returns the CLS band name for a given score.
    Args:
        score (float): CLS score 0–100
    Returns:
        str: "GREEN", "AMBER", or "RED"
    """
    if score < CLS_AMBER[0]:
        return "GREEN"
    elif score < CLS_RED[0]:
        return "AMBER"
    else:
        return "RED"


# ==============================================================
# MAIN CLS FUNCTION
# ==============================================================

def compute_cls(ear, head_pitch, blink_rate, movement_var, temp, baseline):
    """
    Computes the Cognitive Load Score (CLS) from face + biosignal inputs.
    Pure maths formula — no ML model involved at this stage.

    Args:
        ear          (float) : Eye Aspect Ratio — from face_pipeline.py
                               Normal ~0.28–0.32 | Low = drowsy
        head_pitch   (float) : Forward head tilt in degrees
                               Normal ~0–10 | High = inattentive
        blink_rate   (float) : Blinks per minute
                               Normal ~15–20 | High = fatigue
        movement_var (float) : Variance in operator movement
                               Replaces HRV + grip from original spec
                               From MPU6050 sensor via ESP32
        temp         (float) : Cabin temperature in Celsius from DHT11
                               Above 35°C adds fatigue multiplier
        baseline     (dict)  : Operator's personal baseline with keys:
                               'ear'      — their normal EAR
                               'move_max' — their normal movement max

    Returns:
        score (float) : CLS score 0–100
                        0–39  = GREEN (safe)
                        40–69 = AMBER (warning)
                        70+   = RED   (critical)

    Formula Breakdown:
        ear_dev   = how much eyes have closed vs baseline (0–1)
        pitch_dev = how far head has tilted forward (0–1)
        blink_dev = blink rate normalized to 30 bpm max (0–1)
        move_dev  = movement variance vs baseline max (0–1)
        temp_mult = 1.2 if cabin > 35°C else 1.0
        fatigue   = weighted combo of eye + blink + movement → 0–60
        attention = head pitch deviation → 0–40
        CLS       = (fatigue×0.65 + attention×0.35) × temp_mult
    """

    # --- Deviation calculations ---

    # How much has EAR dropped below the operator's baseline?
    # max(0, ...) ensures no negative values
    ear_dev = max(0, (baseline["ear"] - ear) / baseline["ear"])

    # How far has head pitched forward beyond 10° normal threshold?
    # Normalized to 30° range
    pitch_dev = max(0, (head_pitch - 10) / 30)

    # Blink rate normalized — 30 blinks/min is high fatigue ceiling
    blink_dev = min(blink_rate / 30, 1)

    # Movement variance vs baseline maximum
    move_dev = min(movement_var / baseline["move_max"], 1)

    # --- Temperature multiplier ---
    # Cabin above 35°C increases fatigue by 20%
    temp_mult = 1.2 if temp > 35 else 1.0

    # --- Fatigue score (0–60) ---
    # Weighted: eye openness 45%, blink rate 25%, movement 30%
    fatigue = (ear_dev * 0.45 + blink_dev * 0.25 + move_dev * 0.30) * 60

    # --- Attention score (0–40) ---
    # Head pitch forward = loss of attention
    attention = pitch_dev * 40

    # --- Final CLS (0–100) ---
    score = (fatigue * 0.95 + attention * 0.55) * temp_mult
    score = min(100, score)

    return round(score, 2)


# ==============================================================
# BREAKDOWN HELPER — shows contribution of each component
# ==============================================================

def compute_cls_detailed(ear, head_pitch, blink_rate,
                          movement_var, temp, baseline):
    """
    Same as compute_cls() but returns a full breakdown dict.
    Useful for debugging and dashboard display.
    """
    ear_dev   = max(0, (baseline["ear"] - ear) / baseline["ear"])
    pitch_dev = max(0, (head_pitch - 10) / 30)
    blink_dev = min(blink_rate / 30, 1)
    move_dev  = min(movement_var / baseline["move_max"], 1)
    temp_mult = 1.2 if temp > 35 else 1.0
    fatigue   = (ear_dev * 0.45 + blink_dev * 0.25 + move_dev * 0.30) * 60
    attention = pitch_dev * 40
    score     = min(100, (fatigue * 0.65 + attention * 0.35) * temp_mult)

    return {
        "cls_score"   : round(score, 2),
        "band"        : get_cls_band(score),
        "ear_dev"     : round(ear_dev,   3),
        "pitch_dev"   : round(pitch_dev, 3),
        "blink_dev"   : round(blink_dev, 3),
        "move_dev"    : round(move_dev,  3),
        "temp_mult"   : temp_mult,
        "fatigue"     : round(fatigue,   2),
        "attention"   : round(attention, 2),
    }


# ==============================================================
# QUICK TEST — Run this file directly
# python cognitive_engine/cls_engine.py
# ==============================================================

if __name__ == "__main__":

    print("=" * 55)
    print("  RYVA — CLS Engine Test")
    print("=" * 55)

    # --- Test 1: FATIGUED operator (should return > 60) ---
    fatigued = compute_cls_detailed(
        ear          = 0.17,   # Eyes drooping
        head_pitch   = 22,     # Head tilted forward
        blink_rate   = 26,     # High blink rate
        movement_var = 70,     # High movement variance
        temp         = 36,     # Hot cabin — multiplier active
        baseline     = DEFAULT_BASELINE
    )

    print("\n🔴 Test 1 — Fatigued Operator")
    print(f"   EAR=0.17 | Pitch=22° | Blinks=26/min | Temp=36°C")
    for key, val in fatigued.items():
        print(f"   {key:<14} : {val}")
    assert fatigued["cls_score"] > 60, \
        f"FAILED — expected > 60, got {fatigued['cls_score']}"
    print(f"   ✅ PASSED — CLS = {fatigued['cls_score']} (above 60)")

    # --- Test 2: HEALTHY operator (should return < 35) ---
    healthy = compute_cls_detailed(
        ear          = 0.30,   # Eyes wide open
        head_pitch   = 5,      # Head upright
        blink_rate   = 14,     # Normal blink rate
        movement_var = 20,     # Steady movement
        temp         = 28,     # Normal cabin temp
        baseline     = DEFAULT_BASELINE
    )

    print("\n🟢 Test 2 — Healthy Operator")
    print(f"   EAR=0.30 | Pitch=5° | Blinks=14/min | Temp=28°C")
    for key, val in healthy.items():
        print(f"   {key:<14} : {val}")
    assert healthy["cls_score"] < 35, \
        f"FAILED — expected < 35, got {healthy['cls_score']}"
    print(f"   ✅ PASSED — CLS = {healthy['cls_score']} (below 35)")

    # --- Test 3: AMBER zone ---
    amber = compute_cls_detailed(
        ear          = 0.24,
        head_pitch   = 15,
        blink_rate   = 20,
        movement_var = 40,
        temp         = 33,
        baseline     = DEFAULT_BASELINE
    )
    print("\n🟡 Test 3 — Amber Zone Operator")
    print(f"   EAR=0.24 | Pitch=15° | Blinks=20/min | Temp=33°C")
    print(f"   CLS Score : {amber['cls_score']} — Band: {amber['band']}")

    print("\n" + "=" * 55)
    print("  All tests passed ✅")
    print("=" * 55)
