#Module for the Bearded Dragons

SPECIES_NAME = "Bearded Dragon"
CATEGORY = "Lizards"
# Days to wait before offering food again after a regurgitation event.
# Bearded dragons: withhold food 3-5 days, then reintroduce small easy prey. 5 days is safe.
REGURG_WAIT_DAYS = 5

def get_feeder_recommendation(weight):
    # Weight parameter is ignored; recommendations are stage/size-based.
    return (
        "<strong>Hatchlings (0-3 months)</strong><br>"
        "• Insects 1x/day, as many as dragon will eat<br>"
        "• Vegetables daily, as much as dragon will eat<br>"
        "• Calcium powder on all insects and salads<br>"
        "• Multivitamin powder on salads 2x/week<br><br>"

        "<strong>Juveniles (&lt;12\" / 25 cm)</strong><br>"
        "• 5-6 head-sized insects daily, or equivalent portion<br>"
        "• Vegetables daily (≈3x insect volume)<br>"
        "• Calcium powder on all insects and salads<br>"
        "• Multivitamin powder on salads 2x/week<br><br>"

        "<strong>Subadults &amp; Adults (&gt;12\" / 25 cm)</strong><br>"
        "• 3-4 head-sized insects 2x/week, or equivalent portion<br>"
        "• Vegetables 3x/week (one portion = head size)<br>"
        "• Calcium powder on all insects and salads<br>"
        "• Multivitamin powder on salads 1x/week<br><br>"

        "<strong>Gravid females</strong><br>"
        "• 4-5 head-sized insects 2x/week, or equivalent portion<br>"
        "• Vegetables 3x/week (one portion = head size)<br>"
        "• Calcium powder on all insects and salads<br>"
        "• Multivitamin powder on salads 2x/week<br><br>"

        "<em>Hatchlings require 60-80 % protein, juveniles ≈60 %, adults 15-30 %.</em><br>"
    )
