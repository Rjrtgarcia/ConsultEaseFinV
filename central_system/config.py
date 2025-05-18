"""
Central configuration management for ConsultEase.
Provides a unified interface for accessing configuration settings from various sources.
"""
import os
import json
import logging
import pathlib

logger = logging.getLogger(__name__)

class Config:
    """Central configuration management for ConsultEase."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "database": {
            "type": "sqlite",
            "host": "localhost",
            "port": 5432,
            "name": "consultease",
            "user": "",
            "password": "",
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800
        },
        "mqtt": {
            "broker_host": "localhost",
            "broker_port": 1883,
            "use_tls": False,
            "username": "",
            "password": "",
            "client_id": "central_system"
        },
        "ui": {
            "fullscreen": True,
            "transition_type": "fade",
            "transition_duration": 300,
            "theme": "default"
        },
        "keyboard": {
            "type": "squeekboard",
            "fallback": "onboard"
        },
        "security": {
            "min_password_length": 8,
            "password_lockout_threshold": 5,
            "password_lockout_duration": 900,  # 15 minutes in seconds
            "session_timeout": 1800  # 30 minutes in seconds
        },
        "logging": {
            "level": "INFO",
            "file": "consultease.log",
            "max_size": 10485760,  # 10MB
            "backup_count": 5
        }
    }
    
    # Singleton instance
    _instance = None
    _config = None
    
    @classmethod
    def instance(cls):
        """Get the singleton instance of the configuration manager."""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager."""
        # Prevent multiple initialization of the singleton
        if Config._instance is not None:
            return
            
        # Load configuration
        self._config = self.load()
    
    @classmethod
    def load(cls):
        """Load configuration from file or environment."""
        config = cls.DEFAULT_CONFIG.copy()
        
        # Try to load from config file
        config_paths = [
            os.environ.get('CONSULTEASE_CONFIG'),
            'config.json',
            os.path.join(os.path.dirname(__file__), 'config.json'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        ]
        
        for config_path in config_paths:
            if config_path and os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        file_config = json.load(f)
                        # Update config with file values
                        cls._update_dict(config, file_config)
                    logger.info(f"Loaded configuration from {config_path}")
                    break
                except Exception as e:
                    logger.error(f"Failed to load configuration from {config_path}: {e}")
        
        # Override with environment variables
        cls._override_from_env(config)
        
        return config
    
    @staticmethod
    def _update_dict(target, source):
        """
        Recursively update a dictionary with values from another dictionary.
        
        Args:
            target (dict): Target dictionary to update
            source (dict): Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                Config._update_dict(target[key], value)
            else:
                target[key] = value
    
    @staticmethod
    def _override_from_env(config):
        """
        Override configuration values from environment variables.
        
        Args:
            config (dict): Configuration dictionary to update
        """
        # Database configuration
        if 'DB_TYPE' in os.environ:
            config['database']['type'] = os.environ['DB_TYPE']
        if 'DB_HOST' in os.environ:
            config['database']['host'] = os.environ['DB_HOST']
        if 'DB_PORT' in os.environ:
            config['database']['port'] = int(os.environ['DB_PORT'])
        if 'DB_NAME' in os.environ:
            config['database']['name'] = os.environ['DB_NAME']
        if 'DB_USER' in os.environ:
            config['database']['user'] = os.environ['DB_USER']
        if 'DB_PASSWORD' in os.environ:
            config['database']['password'] = os.environ['DB_PASSWORD']
        if 'DB_POOL_SIZE' in os.environ:
            config['database']['pool_size'] = int(os.environ['DB_POOL_SIZE'])
        if 'DB_MAX_OVERFLOW' in os.environ:
            config['database']['max_overflow'] = int(os.environ['DB_MAX_OVERFLOW'])
        
        # MQTT configuration
        if 'MQTT_BROKER_HOST' in os.environ:
            config['mqtt']['broker_host'] = os.environ['MQTT_BROKER_HOST']
        if 'MQTT_BROKER_PORT' in os.environ:
            config['mqtt']['broker_port'] = int(os.environ['MQTT_BROKER_PORT'])
        if 'MQTT_USERNAME' in os.environ:
            config['mqtt']['username'] = os.environ['MQTT_USERNAME']
        if 'MQTT_PASSWORD' in os.environ:
            config['mqtt']['password'] = os.environ['MQTT_PASSWORD']
        
        # UI configuration
        if 'CONSULTEASE_FULLSCREEN' in os.environ:
            config['ui']['fullscreen'] = os.environ['CONSULTEASE_FULLSCREEN'].lower() in ('true', 'yes', '1')
        if 'CONSULTEASE_THEME' in os.environ:
            config['ui']['theme'] = os.environ['CONSULTEASE_THEME']
        
        # Keyboard configuration
        if 'CONSULTEASE_KEYBOARD' in os.environ:
            config['keyboard']['type'] = os.environ['CONSULTEASE_KEYBOARD']
    
    def get(self, key, default=None):
        """
        Get a configuration value by key.
        
        Args:
            key (str): Configuration key (dot notation for nested keys)
            default: Default value if key is not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """
        Set a configuration value by key.
        
        Args:
            key (str): Configuration key (dot notation for nested keys)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self, config_path=None):
        """
        Save the configuration to a file.
        
        Args:
            config_path (str, optional): Path to save the configuration file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not config_path:
            config_path = os.environ.get('CONSULTEASE_CONFIG', 'config.json')
        
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(config_path)), exist_ok=True)
            
            # Write configuration to file
            with open(config_path, 'w') as f:
                json.dump(self._config, f, indent=4)
            
            logger.info(f"Saved configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            return False

# Convenience function to get the configuration instance
def get_config():
    """Get the configuration instance."""
    return Config.instance()
