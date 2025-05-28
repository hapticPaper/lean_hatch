#!/usr/bin/env python3
"""
Test script for Twilio response handlers.
Demonstrates how to use TwilioResponseHandler to convert JSON responses to Pydantic models.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_model.api_message_handler import TwilioHeaderHandler, TwilioSMSResponseHandler
from utils import logger

# Sample Twilio response JSON (typical response from Twilio API)
sample_twilio_response = {
    "account_sid": "ACd67d920e2f8354696051a98d2d444815",
    "api_version": "2010-04-01",
    "body": "Test message from Hatch!",
    "date_created": "2024-01-15T10:30:00Z",
    "date_sent": "2024-01-15T10:30:05Z", 
    "date_updated": "2024-01-15T10:30:05Z",
    "direction": "outbound-api",
    "error_code": None,
    "error_message": None,
    "from": "+18333450761",
    "messaging_service_sid": None,
    "num_media": 0,
    "num_segments": 1,
    "price": "-0.0075",
    "price_unit": "USD",
    "sid": "SM1234567890abcdef1234567890abcdef",
    "status": "sent",
    "subresource_uris": {
        "media": "/2010-04-01/Accounts/ACd67d920e2f8354696051a98d2d444815/Messages/SM1234567890abcdef1234567890abcdef/Media.json"
    },
    "to": "+18777804236",
    "uri": "/2010-04-01/Accounts/ACd67d920e2f8354696051a98d2d444815/Messages/SM1234567890abcdef1234567890abcdef.json"
}

# Sample response headers from Twilio API
sample_response_headers = {
    "content-type": "application/json",
    "content-length": "1234",
    "connection": "keep-alive",
    "date": "2024-01-15T10:30:00Z",
    "twilio-concurrent-requests": "5",
    "twilio-request-id": "RQ1234567890abcdef1234567890abcdef",
    "twilio-request-duration": "0.256",
    "x-home-region": "us1",
    "x-api-domain": "api.twilio.com",
    "strict-transport-security": "max-age=31536000; includeSubDomains",
    "x-cache": "Miss from cloudfront",
    "via": "1.1 cloudfront.net (CloudFront)",
    "x-amz-cf-pop": "SEA19-C1",
    "x-amz-cf-id": "ABCDEFGHIJKLMNOP-1234567890",
    "x-powered-by": "AT&T"
}

def test_twilio_handlers():
    """Test the Twilio response handlers."""
    logger.info("Testing Twilio response handlers...")
    
    try:
        # Test individual handlers
        logger.info("Testing SMS response handler...")
        sms_response = TwilioSMSResponseHandler.from_response_dict(sample_twilio_response)
        logger.info("SMS Response model created successfully", 
                   sid=sms_response.sid, 
                   status=sms_response.status,
                   to=sms_response.to,
                   from_=sms_response.from_)
        
        logger.info("Testing response headers handler...")
        response_headers = TwilioHeaderHandler.from_headers_dict(sample_response_headers)
        logger.info("Response headers model created successfully",
                   content_type=response_headers.content_type,
                   request_id=response_headers.twilio_request_id,
                   duration=response_headers.twilio_request_duration)
        
        # Test complete pipeline
        logger.info("Testing complete response processing pipeline...")
        sms_response_complete, headers_complete = TwilioSMSResponseHandler.process_sms_response(
            sample_twilio_response, sample_response_headers
        )
        
        logger.info("Complete pipeline test successful",
                   message_sid=sms_response_complete.sid,
                   message_status=sms_response_complete.status,
                   request_duration=headers_complete.twilio_request_duration)
        
        # Display models as JSON for verification
        logger.info("SMS Response Model JSON", data=sms_response_complete.dict())
        logger.info("Headers Model JSON", data=headers_complete.dict())
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Twilio handlers: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_twilio_handlers()
    if success:
        logger.info("All Twilio handler tests passed!")
    else:
        logger.error("Twilio handler tests failed!")
        sys.exit(1)
