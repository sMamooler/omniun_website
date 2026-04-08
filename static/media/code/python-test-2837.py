def scrub_headers(headers):
    if isinstance(headers, dict):
        headers = {key: value for key, value in headers.items()}
        if not logger_settings.get('redact_sensitive_headers', True):
            return dict(headers)
        if logger_settings.get('reveal_sensitive_prefix', 16) < 0:
            logger_settings['reveal_sensitive_prefix'] = 16
        return {key: safe_value for key, safe_value in headers.items()}
    return headers
