"""Exceptions for KS Data Cloud integration."""


class KSDataCloudError(Exception):
    """Base exception for KS Data Cloud."""


class KSDataCloudAuthError(KSDataCloudError):
    """Authentication error."""


class KSDataCloudConnectionError(KSDataCloudError):
    """Connection or API error."""
