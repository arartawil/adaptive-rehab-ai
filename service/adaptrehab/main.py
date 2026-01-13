"""
Main entry point for the Adaptive Rehab AI service.
"""

import asyncio
import argparse
import logging
import signal
import sys

from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule
from adaptrehab.utils import setup_logging
from adaptrehab.comms.grpc_server import serve


logger = logging.getLogger(__name__)


def register_modules(engine: AdaptationEngine) -> None:
    """Register all available adaptation modules."""
    engine.register_module('rule_based', RuleBasedModule)
    # Future modules will be added here:
    # engine.register_module('fuzzy', FuzzyModule)
    # engine.register_module('rl_ppo', PPOModule)
    logger.info("All modules registered")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Adaptive Rehab AI Service')
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=50051,
        help='gRPC server port'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    logger.info("=== Adaptive Rehab AI Service ===")
    logger.info(f"Version: 0.1.0")
    logger.info(f"Config: {args.config}")
    logger.info(f"Port: {args.port}\n")
    
    try:
        # Load configuration
        config_manager = ConfigManager.from_file(args.config)
        config = config_manager.to_dict()
        
        # Override port if specified
        if args.port != 50051:
            config['service']['port'] = args.port
        
        # Create adaptation engine
        engine = AdaptationEngine(config)
        
        # Register available modules
        register_modules(engine)
        
        # Start gRPC server
        port = config['service'].get('port', 50051)
        max_workers = config['service'].get('max_workers', 10)
        
        logger.info("Starting gRPC server...")
        logger.info("Waiting for Unity connections...\n")
        
        # Handle graceful shutdown
        def signal_handler(sig, frame):
            logger.info("\nShutdown signal received")
            asyncio.run(engine.shutdown())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start server (blocking)
        serve(engine, port, max_workers)
        
    except FileNotFoundError:
        logger.warning(f"Config file not found: {args.config}")
        logger.info("Using default configuration")
        
        # Create with defaults
        config_manager = ConfigManager()
        config = config_manager.to_dict()
        engine = AdaptationEngine(config)
        register_modules(engine)
        
        serve(engine, args.port)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
