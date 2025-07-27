class Service:
    """Base class for services."""

    name = None

    def __init__(self):
        """Initialize the service class."""
        self._client = None
        if self.name is None:
            raise RuntimeError("Service name attribute must be set.")

    @property
    def client(self):
        """Get the client for the service."""
        if self._client is None:
            self._client = self.init()
        return self._client

    def _init(self):
        if self.client is None:
            raise RuntimeError(
                f"Service {self.name} client is not initialized."
                "\n\nYour init method must set self.client."
            )

    def _close(self):
        if self._client is not None:
            self.close()

    def init(self):
        """Override to implement init."""
        raise NotImplementedError("Subclasses must implement init_service")

    def close(self):
        """Override to implement close."""
        raise NotImplementedError("Subclasses must implement close_service")

    def status(self):
        """Override to implement health check."""
        raise NotImplementedError("Subclasses must implement status")
