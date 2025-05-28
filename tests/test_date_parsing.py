#!/usr/bin/env python3
"""
Quick test for the updated date parsing in twilioHeaderHandler.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from data_model.api_message_handler import twilioHeaderHandler
from utils import logger

# Test headers with the GMT date format
test_headers = {
    "content-type": "application/json",
    "content-length": "1234",
    "connection": "keep-alive",
    "date": "Mon, 26 May 2025 19:22:31 GMT",  # The format you provided
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

def test_date_parsing():
    """Test the date parsing with GMT format."""
    logger.info("Testing date parsing with GMT format...")
    
    try:
        # Test 1: Header handler
        headers_model = twilioHeaderHandler.from_headers_dict(test_headers)
        
        logger.info("Headers model created successfully",
                   parsed_date=headers_model.date.isoformat(),
                   original_date=test_headers["date"],
                   request_id=headers_model.twilio_request_id)
        
        # Verify the date was parsed correctly
        expected_year = 2025
        expected_month = 5
        expected_day = 26
        
        if (headers_model.date.year == expected_year and 
            headers_model.date.month == expected_month and 
            headers_model.date.day == expected_day):
            logger.info("Header date parsing test PASSED!", 
                       parsed_date=headers_model.date.isoformat())
        else:
            logger.error("Header date parsing test FAILED!",
                        expected_date=f"{expected_year}-{expected_month:02d}-{expected_day:02d}",
                        actual_date=headers_model.date.isoformat())
            return False
        
        # Test 2: SMS Response handler with same date format
        logger.info("Testing SMS response handler date parsing...")
        sms_response_dict = {
            'account_sid': 'AC123',
            'api_version': '2010-04-01',
            'body': 'Test message',
            'date_created': "Mon, 26 May 2025 19:22:31 GMT",
            'date_sent': "Mon, 26 May 2025 19:22:31 GMT",
            'date_updated': "Mon, 26 May 2025 19:22:31 GMT",
            'direction': 'outbound-api',
            'from': '+1234567890',
            'to': '+0987654321',
            'sid': 'SM123',
            'status': 'sent',
            'subresource_uris': {},
            'uri': '/test',
            'num_media': 0,
            'num_segments': 1
        }
        
        sms_model = twilioSMSResponseHandler.from_response_dict(sms_response_dict)
        
        # Verify SMS dates were parsed correctly
        if (sms_model.date_created.year == expected_year and
            sms_model.date_created.month == expected_month and 
            sms_model.date_created.day == expected_day):
            logger.info("SMS response date parsing test PASSED!",
                       date_created=sms_model.date_created.isoformat(),
                       date_sent=sms_model.date_sent.isoformat() if sms_model.date_sent else None)
        else:
            logger.error("SMS response date parsing test FAILED!",
                        expected_date=f"{expected_year}-{expected_month:02d}-{expected_day:02d}",
                        actual_date=sms_model.date_created.isoformat())
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error testing date parsing: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_date_parsing()
    if success:
        logger.info("Date parsing test completed successfully!")
    else:
        logger.error("Date parsing test failed!")
        sys.exit(1)
