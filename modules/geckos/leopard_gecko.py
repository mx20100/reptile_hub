#Module for the leopard geckos

SPECIES_NAME = "Leopard Gecko"
CATEGORY = "Geckos"
# Days to wait before offering food again after a regurgitation event.
# Leopard geckos: 5-7 days; 7 days is the standard recommendation.
REGURG_WAIT_DAYS = 7

def get_feeder_recommendation(weight):
    # Weight parameter can be ignored to recommend certain insects to geckos which are not based on weight.
    return (
        "Staple Insects: Dubia/Discoid roaches, Crickets, Mealworms, Grasshoppers.<br>"
        "Treats (Rarely): Waxworms, Hornworms.<br>"
        "<em>Note: Always dust insects with calcium/vitamins!</em>"
    )