"""
This type stub file was generated by pyright.
"""

_data = ...
class SQL:
    """Wrap SQLAlchemy to provide a simple SQL API."""
    def __init__(self, url, **kwargs) -> None:
        """
        Create instance of sqlalchemy.engine.Engine.

        URL should be a string that indicates database dialect and connection arguments.

        http://docs.sqlalchemy.org/en/latest/core/engines.html#sqlalchemy.create_engine
        http://docs.sqlalchemy.org/en/latest/dialects/index.html
        """
        ...
    
    def __del__(self): # -> None:
        """Disconnect from database."""
        ...
    
    @_enable_logging
    def execute(self, sql, *args, **kwargs):
        """Execute a SQL statement."""
        ...
    


