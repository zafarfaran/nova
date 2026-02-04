"""Configuration helper for logging per section."""

import logging

from app.config import get_settings


def is_logging_enabled(section: str) -> bool:
    """Check if logging is enabled for a given section.
    
    Args:
        section: Section name (e.g., "document_processing", "chat")
        
    Returns:
        True if logging should be enabled for this section
    """
    settings = get_settings()
    return settings.is_logging_enabled_for_section(section)


def get_log_level_for_section(section: str) -> int:
    """Get the log level (as logging constant) for a given section.
    
    Args:
        section: Section name (e.g., "document_processing", "chat")
        
    Returns:
        Logging level constant (logging.DEBUG, logging.INFO, etc.)
    """
    settings = get_settings()
    level_str = settings.get_log_level_for_section(section)
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    return level_map.get(level_str.upper(), logging.INFO)


def should_log(section: str, level: int) -> bool:
    """Check if a log entry should be emitted for a section at a given level.
    
    Args:
        section: Section name
        level: Log level (logging.DEBUG, logging.INFO, etc.)
        
    Returns:
        True if the log should be emitted
    """
    if not is_logging_enabled(section):
        return False
    
    section_level = get_log_level_for_section(section)
    return level >= section_level
