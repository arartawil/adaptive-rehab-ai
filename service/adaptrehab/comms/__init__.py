"""Communication layer - gRPC server and message handling"""

from adaptrehab.comms.grpc_server import serve, AdaptationServicer

__all__ = ["serve", "AdaptationServicer"]
