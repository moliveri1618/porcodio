# Defines dependencies used by the routers
import os

def setup_imports():
    """
    Dynamically import modules based on the environment.
    Returns a dictionary of imported modules.
    """
    modules = {}
    
    if "GITHUB_ACTIONS" in os.environ:
        # GitHub Actions environment
        from api.routers import items
        modules["items"] = items
    else:
        # Local or AWS Lambda environment
        from routers import items
        modules["items"] = items
    
    return modules