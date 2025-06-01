def sample_function():
    """
    A sample function that demonstrates good practices.
    
    Returns:
        str: A greeting message
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Generating greeting")
    return "Hello, World!"