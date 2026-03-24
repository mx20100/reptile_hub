# Module for ball pythons

SPECIES_NAME = "Ball Python"
CATEGORY = "Snakes"

def get_feeder_recommendation(weight):
    """Return feeding guidance based on the animal's weight.

    The rules are:
      * juveniles (0-12 mo or until ≈500g): 10-15% BW every 7d
      * subadults (≈12-24 mo or until weight stabilises): up to 7% BW
        every 14-20d
      * adults: up to 5% BW every 20-30d (or 6 % every 30-40d)
    """
    try:
        w = float(weight)
        # juveniles/growers
        if w < 500:
            return {"size": "10-15% of body weight", "percent_min": 0.10, "percent_max": 0.15, "qty": 1, "freq": "7 days"}
        # sub‑adult
        elif w < 1500:
            return {"size": "up to 7% of body weight", "percent_min": 0.05, "percent_max": 0.07, "qty": 1, "freq": "14-20 days"}
        # adults
        else:
            return {"size": "up to 5% of body weight", "percent_min": 0.04, "percent_max": 0.05, "qty": 1, "freq": "20-30 days"}
    except (ValueError, TypeError):
        pass
    return None
