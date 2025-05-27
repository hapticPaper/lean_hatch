# py_services/utils/exceptions.py
"""
Custom exceptions for the service layer.
"""

class ServiceException(Exception):
    """Base class for service layer exceptions."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "SERVICE_ERROR"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class DatabaseError(ServiceException):
    """For database-related errors not caught by SQLAlchemyError handler."""
    def __init__(self, message: str = "A database error occurred.", status_code: int = 500, error_code: str = "DATABASE_ERROR"):
        super().__init__(message, status_code, error_code)

# --- Email Service Exceptions ---
class EmailServiceError(ServiceException):
    """Base class for email service exceptions."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "EMAIL_SERVICE_ERROR"):
        super().__init__(message, status_code, error_code)

class EmailSendFailedError(EmailServiceError):
    """Raised when an email fails to send via the provider."""
    def __init__(self, message: str = "Failed to send email.", provider_status_code: int = None, status_code: int = 502, error_code: str = "EMAIL_SEND_FAILED"):
        super().__init__(message, status_code, error_code)
        self.provider_status_code = provider_status_code

class InvalidEmailRecipientError(EmailServiceError):
    """Raised when the recipient email address is invalid or not provided."""
    def __init__(self, message: str = "Invalid or missing email recipient.", status_code: int = 400, error_code: str = "INVALID_EMAIL_RECIPIENT"):
        super().__init__(message, status_code, error_code)

# --- SMS Service Exceptions ---
class SMSServiceError(ServiceException):
    """Base class for SMS service exceptions."""
    def __init__(self, message: str, status_code: int = 500, error_code: str = "SMS_SERVICE_ERROR"):
        super().__init__(message, status_code, error_code)

class SMSSendFailedError(SMSServiceError):
    """Raised when an SMS fails to send via the provider."""
    def __init__(self, message: str = "Failed to send SMS.", provider_error_code: str = None, status_code: int = 502, error_code: str = "SMS_SEND_FAILED"):
        super().__init__(message, status_code, error_code)
        self.provider_error_code = provider_error_code

class InvalidPhoneNumberError(SMSServiceError):
    """Raised when the phone number is invalid."""
    def __init__(self, message: str = "Invalid phone number.", status_code: int = 400, error_code: str = "INVALID_PHONE_NUMBER"):
        super().__init__(message, status_code, error_code)

