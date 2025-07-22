import pulumi
import pulumi_aws as aws
import logging
import os

# Set default log level to LOG_LEVEL environment variable. This ensures the default level can be overridden if needed.
# Use constant LOG_LEVELS to specify valid logging levels.
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

def get_log_level_from_env() -> str:
    global log_level
    if log_level not in LOG_LEVELS:
        print(f"Warning: Invalid LOG_LEVEL set '{log_level}'. Defaulting to 'INFO'.")
        log_level = 'INFO'
    
    return log_level

def config_logging() -> logging.Logger:
    logging.basicConfig(
        level=get_log_level_from_env(),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler()
        ]  
    )
    return logging.getLogger(__name__)

def get_global_tags() -> dict:
    config = pulumi.Config()
    return config.get_object("globalTags") or {}
    

def merge_tags(resource_name: str, additional_tags: dict = None) -> dict:
    """Helper to merge global tags with resource-specific tags."""
    tags = {
        **get_global_tags(),
        "Name": resource_name
    }

    if additional_tags:
        tags.update(additional_tags)

    return tags
