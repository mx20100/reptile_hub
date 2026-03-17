#Module for the Crested geckos

SPECIES_NAME = "Crested Gecko"
CATEGORY = "Geckos"

def get_feeder_recommendation(weight):
    # Weight parameter can be ignored to recommend certain insects to geckos which are not based on weight.
    return (
        "Staple food: Gecko Nutrition powdered food<br>"
        "Treats: Crickets, Grasshoppers, Dubias.<br>"
        "<em>Note: Always dust insects with calcium/vitamins!</em>"
    )