from docketanalyzer import Registry

from .service import Service


class ServiceRegistry(Registry):
    """Registry for service classes."""

    def find_filter(self, obj):
        """Find filter for service classes."""
        return isinstance(obj, type) and issubclass(obj, Service) and obj is not Service


services = ServiceRegistry()
services.find()


def load_clients(*client_names: str, return_service: bool = False):
    """Load clients from the service registry."""
    service_map = {x.name: x for x in services}

    clients = [
        service_map[client_name]()
        if return_service
        else service_map[client_name]().client
        for client_name in client_names
    ]

    return clients if len(clients) > 1 else clients[0]
