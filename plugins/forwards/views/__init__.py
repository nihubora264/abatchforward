# Import all view handlers to register them
from . import create
from . import list
from . import view
from . import delete
from . import cancel

# Export all handlers
__all__ = ["create", "list", "view", "delete", "cancel"]
