"""
ETag Middleware for UKG.

Provides conditional request support using MD5 hashes of response data.
"""
import hashlib
import logging
from flask import request, make_response

logger = logging.getLogger(__name__)

def etag_middleware():
    """
    Middleware to add ETag headers for conditional requests.
    
    Supports If-None-Match header for GET requests, returning
    304 Not Modified when content hasn't changed.
    """
    def add_etag(response):
        try:
            # Only add ETags for successful GET/HEAD requests with content
            if request.method in ('GET', 'HEAD') and response.status_code == 200:
                # Generate ETag from response data
                if response.data:
                    etag = hashlib.md5(response.data).hexdigest()
                    response.headers['ETag'] = f'"{etag}"'
                    
                    # Check If-None-Match header
                    if_none_match = request.headers.get('If-None-Match')
                    if if_none_match:
                        # Strip quotes and compare
                        client_etag = if_none_match.strip('"')
                        if client_etag == etag:
                            # Content hasn't changed, return 304
                            return make_response('', 304)
            
            # Add Cache-Control for API responses
            if '/api/' in request.path:
                if 'Cache-Control' not in response.headers:
                    response.headers['Cache-Control'] = 'private, max-age=0, must-revalidate'
                    
        except Exception as e:
            logger.error(f"Error in ETag middleware: {str(e)}")
            
        return response
    
    return add_etag
