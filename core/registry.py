# 1. Import your animal modules
from modules.snakes import ball_python, plains_hognose
from modules.geckos import leopard_gecko
from modules.snakes import ball_python
from modules.lizards import bearded_dragon
from modules.geckos import crested_gecko

# 2. Register any new animals here.
ANIMAL_MODULES = {
    plains_hognose.SPECIES_NAME: plains_hognose,
    leopard_gecko.SPECIES_NAME: leopard_gecko,
    ball_python.SPECIES_NAME: ball_python,
    bearded_dragon.SPECIES_NAME: bearded_dragon,
    crested_gecko.SPECIES_NAME: crested_gecko
}

def get_regurg_wait(species_name):
    """Return the number of days to wait after a regurgitation event for this species."""
    module = ANIMAL_MODULES.get(species_name)
    return getattr(module, 'REGURG_WAIT_DAYS', 14)  # 14 days is a safe default


def calculate_feeder(species_name, weight):
    """Finds the correct animal module and runs its specific math."""
    module = ANIMAL_MODULES.get(species_name)
    
    # If the module exists and has a feeder calculator, run it!
    if module and hasattr(module, 'get_feeder_recommendation'):
        return module.get_feeder_recommendation(weight)
    
    return None

def get_available_species():
    """Builds a dictionary of categories and available species."""
    catalog = {}
    for species, module in ANIMAL_MODULES.items():
        # Look for the CATEGORY variable in the module, default to 'Other' if missing
        cat = getattr(module, 'CATEGORY', 'Other')
        
        if cat not in catalog:
            catalog[cat] = []
            
        catalog[cat].append(species)
        
    return catalog