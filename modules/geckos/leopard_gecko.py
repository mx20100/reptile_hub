#Module for the leopard geckos

SPECIES_NAME = "Leopard Gecko"
CATEGORY = "Geckos"

def get_feeder_recommendation(weight):
    # Weight parameter can be ignored to recommend certain insects to geckos which are not based on weight.
    return (
        "Staple Insects: Dubia/Discoid roaches, Crickets, Mealworms, Grasshoppers.<br>"
        "Treats (Rarely): Waxworms, Hornworms.<br>"
        "<em>Note: Always dust insects with calcium/vitamins!</em>"
    )