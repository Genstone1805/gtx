"""
Middleware to log all HTTP requests and responses.
"""
import time
import json
import logging
from .utils import get_client_ip

# Get Django logger
logger = logging.getLogger('gtx')


class RequestLoggingMiddleware:
    """
    Middleware to log all HTTP requests and responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get request details
        method = request.method
        path = request.get_full_path()
        user = getattr(request, 'user', None)
        user_email = user.email if user and hasattr(user, 'email') else 'Anonymous'
        ip_address = get_client_ip(request)
        
        # Log request
        start_time = time.time()
        logger.info(f"REQUEST | {method} {path} | User: {user_email} | IP: {ip_address}")
        
        # Log request body for POST/PUT/PATCH
        if method in ['POST', 'PUT', 'PATCH']:
            try:
                # Try to get body content
                if hasattr(request, 'body') and request.body:
                    # Don't log sensitive data
                    if 'password' in path or 'pin' in path or 'token' in path:
                        logger.debug(f"REQUEST BODY | {method} {path} | [SENSITIVE DATA - NOT LOGGED]")
                    else:
                        try:
                            body = request.body.decode('utf-8')[:500]  # Limit to 500 chars
                            logger.debug(f"REQUEST BODY | {method} {path} | {body}...")
                        except:
                            logger.debug(f"REQUEST BODY | {method} {path} | [BINARY DATA]")
            except Exception as e:
                logger.debug(f"REQUEST BODY | Error reading body: {str(e)}")
        
        # Get response
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"RESPONSE | {method} {path} | Status: {response.status_code} | "
            f"Duration: {duration:.3f}s"
        )
        
        # Log errors
        if response.status_code >= 400:
            log_func = logger.warning if response.status_code < 500 else logger.error
            log_func(
                f"ERROR | {method} {path} | Status: {response.status_code} | "
                f"User: {user_email} | Duration: {duration:.3f}s"
            )
        
        return response


class ExceptionLoggingMiddleware:
    """
    Middleware to log all unhandled exceptions.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.exception(
                f"EXCEPTION | {request.method} {request.get_full_path()} | "
                f"User: {getattr(request.user, 'email', 'Anonymous') if hasattr(request, 'user') else 'Unknown'} | "
                f"Error: {str(e)}"
            )
            raise
