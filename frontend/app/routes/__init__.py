# File __init__.py per il package routes
from .cliente_routes import cliente_bp
from .fattura_routes import fattura_bp  
from .costi_routes import costi_bp

__all__ = ['cliente_bp', 'fattura_routes', 'costi_bp']