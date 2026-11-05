from importlib import import_module


def register_models() -> None:
    import_module("clinic_api.db.models.identity.access")
    import_module("clinic_api.db.models.identity.organization")
    import_module("clinic_api.db.models.catalog.facilities")
    import_module("clinic_api.db.models.catalog.people")
    import_module("clinic_api.db.models.catalog.affiliations")
    import_module("clinic_api.db.models.catalog.specialties")
    import_module("clinic_api.db.models.planning.treatment")
    import_module("clinic_api.db.models.planning.availability")
    import_module("clinic_api.db.models.planning.weekly")
