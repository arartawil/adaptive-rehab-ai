"""
Configuration Manager - Handles loading and validation of configurations.
"""

import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages configuration loading, validation, and access.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self._validate_config()
        logger.info("ConfigManager initialized")
    
    @staticmethod
    def from_file(config_path: str) -> 'ConfigManager':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            ConfigManager instance
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from: {config_path}")
            return ConfigManager(config)
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            logger.info("Using default configuration")
            return ConfigManager()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            'service': {
                'port': 50051,
                'max_workers': 10,
                'log_level': 'INFO'
            },
            'adaptation': {
                'update_interval': 0.5,
                'default_module': 'rule_based'
            },
            'safety': {
                'enabled': True,
                'max_change_rate': 0.2,
                'min_confidence': 0.3,
                'bounds': {
                    'difficulty': {
                        'min': 0.0,
                        'max': 1.0
                    }
                }
            },
            'module_configs': {
                'rule_based': {
                    'success_threshold': 0.8,
                    'failure_threshold': 0.4,
                    'increase_step': 0.1,
                    'decrease_step': 0.15
                },
                'fuzzy': {
                    'membership_functions': {
                        'performance': ['poor', 'fair', 'good'],
                        'difficulty': ['easy', 'medium', 'hard']
                    }
                },
                'rl_ppo': {
                    'learning_rate': 0.0003,
                    'gamma': 0.99,
                    'n_steps': 2048,
                    'batch_size': 64
                }
            }
        }
    
    def _validate_config(self) -> None:
        """Validate configuration structure."""
        required_sections = ['service', 'adaptation', 'safety', 'module_configs']
        
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"Missing config section: {section}, using defaults")
                self.config[section] = self._load_default_config()[section]
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'service.port')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., 'service.port')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_module_config(self, module_type: str) -> Dict[str, Any]:
        """Get configuration for specific module type."""
        return self.config.get('module_configs', {}).get(module_type, {})
    
    def save_to_file(self, output_path: str) -> bool:
        """
        Save current configuration to YAML file.
        
        Args:
            output_path: Path to save config file
            
        Returns:
            True if successful
        """
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)
            
            logger.info(f"Configuration saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self.config.copy()
