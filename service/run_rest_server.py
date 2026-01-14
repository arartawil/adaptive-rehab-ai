"""
Run REST API Server for Web Clients

Usage:
    python run_rest_server.py --port 8000
"""

import argparse
import asyncio
import uvicorn
import logging

from adaptrehab.core import AdaptationEngine, ConfigManager
from adaptrehab.modules import RuleBasedModule
from adaptrehab.comms.rest_server import create_rest_server
from adaptrehab.utils import setup_logging


def main():
    parser = argparse.ArgumentParser(description='Adaptive Rehab AI - REST Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--log-level', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("Adaptive Rehab AI - REST Server")
    logger.info("="*60)
    
    # Initialize engine
    config_manager = ConfigManager()
    engine = AdaptationEngine(config_manager.to_dict())
    
    # Register modules
    engine.register_module('rule_based', RuleBasedModule)
    logger.info("✓ Registered module: rule_based")
    
    # Create REST server
    app = create_rest_server(engine)
    
    logger.info(f"\n🚀 Starting REST server on http://{args.host}:{args.port}")
    logger.info(f"📖 API docs: http://localhost:{args.port}/docs")
    logger.info(f"🌐 Open web demo: file:///{__file__.replace('run_rest_server.py', '../web-demo/memory-game.html')}")
    logger.info("\nPress Ctrl+C to stop\n")
    
    # Run server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level=args.log_level.lower()
    )


if __name__ == "__main__":
    main()
