"""
Logging utilities for Ollama integration.

This module provides logging configuration and utilities for tracking
API requests and responses.
"""

import json
import logging
import time
from typing import Any, Dict, Optional, Union


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging for the Ollama integration.
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('ollama_integration.log')
        ]
    )


def log_request(
    logger: logging.Logger,
    method: str,
    url: str,
    params: Optional[Dict] = None,
    data: Optional[Union[Dict, str]] = None,
    headers: Optional[Dict] = None
) -> Dict[str, Any]:
    """Log an outgoing HTTP request.
    
    Args:
        logger: Logger instance
        method: HTTP method
        url: Request URL
        params: Query parameters
        data: Request body
        headers: Request headers
        
    Returns:
        Dictionary containing request context for correlation with response
    """
    context = {
        'request_id': str(id(context)),
        'start_time': time.time(),
        'method': method,
        'url': url
    }
    
    log_data = {
        'event': 'http_request',
        'method': method,
        'url': url,
    }
    
    if params:
        log_data['params'] = params
    if headers:
        log_data['headers'] = {
            k: '*****' if k.lower() in ('authorization', 'api-key') else v
            for k, v in headers.items()
        }
    if data:
        log_data['data'] = data
    
    logger.debug("Outgoing request: %s %s", method, url)
    logger.debug("Request details: %s", json.dumps(log_data, indent=2, default=str))
    
    return context


def log_response(
    logger: logging.Logger,
    context: Dict[str, Any],
    status_code: int,
    headers: Optional[Dict] = None,
    data: Optional[Union[Dict, str]] = None,
    error: Optional[Exception] = None
) -> None:
    """Log an HTTP response.
    
    Args:
        logger: Logger instance
        context: Context from log_request
        status_code: HTTP status code
        headers: Response headers
        data: Response data
        error: Optional exception if the request failed
    """
    duration = time.time() - context.get('start_time', time.time())
    
    log_data = {
        'event': 'http_response',
        'request_id': context.get('request_id'),
        'method': context.get('method'),
        'url': context.get('url'),
        'status_code': status_code,
        'duration_seconds': round(duration, 4)
    }
    
    if headers:
        log_data['headers'] = dict(headers)
    
    if error:
        log_data['error'] = str(error)
        logger.error(
            "Request failed: %s %s - %d in %.2fs - %s",
            context.get('method'),
            context.get('url'),
            status_code,
            duration,
            str(error)
        )
    else:
        log_data['success'] = True
        logger.debug(
            "Request completed: %s %s - %d in %.2fs",
            context.get('method'),
            context.get('url'),
            status_code,
            duration
        )
    
    # Log response data if it's not too large
    if data and isinstance(data, dict):
        log_data['data'] = data
    elif data and isinstance(data, str) and len(data) < 1000:
        log_data['data'] = data
    
    logger.debug("Response details: %s", json.dumps(log_data, indent=2, default=str))
