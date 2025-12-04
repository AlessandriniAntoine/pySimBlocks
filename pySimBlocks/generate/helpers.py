def python_array(x):
    """Convert list → np.array code."""
    return f"np.array({repr(x)})"

def to_camel(name):
    """Convert step → Step, linear_state_space → LinearStateSpace."""
    return "".join(w.capitalize() for w in name.split("_"))

def resolve_class(from_group, type_name):
    """
    Résolution automatique de la classe Python et du module à importer :
    sources: Step, Ramp...
    systems: LinearStateSpace, LpvSystem, ...
    operators: Gain, Sum, Delay, ...
    """
    base = to_camel(type_name)

    if from_group == "sources":
        # Step → Step
        class_name = base
        module = "pySimBlocks.blocks.sources"

    elif from_group == "systems":
        # LinearStateSpace → LinearStateSpace
        class_name = base
        module = "pySimBlocks.blocks.systems"

    elif from_group == "operators":
        # Gain → Gain
        class_name = base
        module = "pySimBlocks.blocks.operators"

    elif from_group == "controllers":
        # StateFeedback → StateFeedback
        class_name = base
        module = "pySimBlocks.blocks.controllers"

    elif from_group == "observers":
        # Luenberger → Luenberger
        class_name = base
        module = "pySimBlocks.blocks.observers"

    else:
        raise ValueError(f"Unknown block group '{from_group}'.")

    return module, class_name
