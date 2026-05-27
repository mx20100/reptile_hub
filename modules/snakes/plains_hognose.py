#Module for the plains/western hognose snake

SPECIES_NAME = "Plains Hognose"
CATEGORY = "Snakes"
# Days to wait before offering food again after a regurgitation event.
# Hognose snakes: 7-10 days; 10 days is the recommended safe minimum.
REGURG_WAIT_DAYS = 10

def get_feeder_recommendation(weight):
    try:
        w = float(weight)
        if w < 4: return {"size": "Under 2g", "qty": 1, "freq": "Consult vet/breeder"}
        elif 4 <= w <= 15: return {"size": "2-3g", "qty": 1, "freq": "4 days"}
        elif 16 <= w <= 23: return {"size": "3-4g", "qty": 2, "freq": "4-5 days"}
        elif 24 <= w <= 30: return {"size": "5-7g", "qty": 1, "freq": "5-6 days"}
        elif 31 <= w <= 50: return {"size": "7-9g", "qty": 1, "freq": "5-6 days"}
        elif 51 <= w <= 90: return {"size": "9-12g", "qty": 1, "freq": "6-7 days"}
        elif 91 <= w <= 170: return {"size": "13-20g", "qty": 1, "freq": "7 days"}
        elif 170 < w <= 300: return {"size": "20-30g", "qty": 1, "freq": "7-10 days"}
        elif w > 300: return {"size": "25+g", "qty": 1, "freq": "10-14 days (non-breeding)"}
    except (ValueError, TypeError):
        pass
    return None