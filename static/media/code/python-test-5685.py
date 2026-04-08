def request_lastfm(method, **kwargs):
    kwargs['method'] = method
    kwargs.setdefault('api_key', API_KEY)
    kwargs.setdefault('format', 'json')
    logger.debug('Calling Last FM method %s' % method)
    logger.debug('Last FM call parameters %s' % kwargs)
    data = request.request_json(ENTRY_POINT, timeout=TIMEOUT, params=kwargs)
    with lastfm_lock:
        if not data:
            logger.error('Error calling Last FM method %s' % method)
            return
        if 'error' in data:
            logger.error('Last FM returned an error %s' % data['message'])
            return
    return data
