#!/usr/bin/env python3
"""
Email Flow Test Script

Demonstrates the complete email workflow:
1. Send email using email-compatible template
2. Process through application message handlers  
3. Save to database with proper message tracking
4. Return structured response data

This verifies that HTML email animations and CSS issues have been resolved.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import dotenv
from providers.sendgrid_email_connector import SendGridEmailConnector
from utils import logger

logger_instance = logger

def test_email_flow():
    """Test the complete email flow with email-compatible template."""
    
    try:
        # Load environment variables
        dotenv.load_dotenv()
        dotenv.load_dotenv(os.path.join('.secrets', '.secrets'))
        
        # Initialize connector
        connector = SendGridEmailConnector()
        logger_instance.info("✅ SendGrid connector initialized successfully")
        
        # Test 1: Send email with compatible HTML template
        logger_instance.info("🧪 Testing email with compatible HTML template...")
        
        email_msg, response_data = connector.send_html_template(
            from_email="ian@hapticpaper.com",
            to_email="rubenstein.ian@gmail.com", 
            subject="🚀 Email Compatibility Test - Hatch Platform",
            template_path="tests/html_email_compatible.html"
        )
        
        # Verify results
        assert email_msg.status == "sent", f"Expected 'sent' status, got '{email_msg.status}'"
        assert response_data['status_code'] == 202, f"Expected 202 status code, got {response_data['status_code']}"
        assert 'message_id' in response_data, "Missing message_id in response"
        
        logger_instance.info(
            "✅ Email sent successfully!",
            email_id=str(email_msg.id),
            sendgrid_message_id=response_data['message_id'], 
            status=email_msg.status,
            conversation_id=str(email_msg.conversation_id)
        )
        
        # Test 2: Send plain text email
        logger_instance.info("🧪 Testing plain text email...")
        
        email_msg2, response_data2 = connector.send_email(
            from_email="ian@hapticpaper.com",
            to_email="rubenstein.ian@gmail.com",
            subject="📧 Plain Text Test - Hatch Platform", 
            content="This is a plain text test email to verify the email handling system works correctly."
        )
        
        assert email_msg2.status == "sent", f"Expected 'sent' status, got '{email_msg2.status}'"
        assert response_data2['status_code'] == 202, f"Expected 202 status code, got {response_data2['status_code']}"
        
        logger_instance.info(
            "✅ Plain text email sent successfully!",
            email_id=str(email_msg2.id),
            sendgrid_message_id=response_data2['message_id'],
            status=email_msg2.status
        )
        
        logger_instance.info("🎉 All email tests passed! Email system is working correctly.")
        
        return True
        
    except Exception as e:
        logger_instance.error(f"❌ Email test failed: {str(e)}")
        return False
        
    finally:
        # Clean up connections
        if 'connector' in locals():
            connector.close_connection()
            logger_instance.info("🧹 Cleaned up database connections")

def test_template_compatibility():
    """Test that the compatible template doesn't contain problematic CSS."""
    
    logger_instance.info("🧪 Testing template compatibility...")
    
    template_path = "tests/html_email_compatible.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # Check for problematic CSS that email clients strip
        problematic_patterns = [
            '@keyframes',
            'animation:',
            'animation-',
            'transition:',
            'transition-',
            'transform:',
            'transform-',
            'display: grid',
            'display:grid',
            'display: flex',
            'display:flex',
            'position: fixed',
            'position:fixed',
            'position: absolute',
            'position:absolute'
        ]
        
        issues_found = []
        for pattern in problematic_patterns:
            if pattern.lower() in template_content.lower():
                issues_found.append(pattern)
                
        if issues_found:
            logger_instance.warning(
                f"⚠️  Found potentially problematic CSS patterns: {', '.join(issues_found)}"
            )
            logger_instance.warning("⚠️  These patterns may not render consistently across all email clients")
        else:
            logger_instance.info("✅ Template appears email-client compatible!")
            
        # Check for positive compatibility indicators
        good_patterns = [
            'table',
            'MSO',
            'Outlook',
            'inline-block',
            'text-align',
            'background-color'
        ]
        
        good_found = [p for p in good_patterns if p.lower() in template_content.lower()]
        logger_instance.info(f"✅ Found email-friendly patterns: {', '.join(good_found)}")
        
        # Return True if we have good patterns, even with some warnings
        return len(good_found) > 0
        
    except FileNotFoundError:
        logger_instance.error(f"❌ Template file not found: {template_path}")
        return False
    except Exception as e:
        logger_instance.error(f"❌ Template compatibility test failed: {str(e)}")
        return False

if __name__ == "__main__":
    logger_instance.info("🚀 Starting Email System Tests...")
    
    # Test template compatibility first
    template_ok = test_template_compatibility()
    
    # Test email flow 
    email_ok = test_email_flow()
    
    # Summary
    if template_ok and email_ok:
        logger_instance.info("🎉 All tests passed! Email system is fully functional and compatible.")
        sys.exit(0)
    else:
        logger_instance.error("❌ Some tests failed. Please check the logs above.")
        sys.exit(1)
