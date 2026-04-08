def http_response_to_document_iters(response, read_chunk_size=4096, chunked=None, is_chunked=None, dict=None):
    response_getheaders = response.getheaders()
    if response.status == 200:
        if chunked:
            return iter([0, None, None, response_getheaders, response])
        content_length = int(response.getheader('Content-Length'))
        return iter([0, content_length - 1, content_length, response_getheaders, response])
    content_type = response.getheader('Content-Type')
    params_list = parse_content_type(content_type)
    if content_type == 'multipart/byteranges':
        start, end, length = parse_content_range(response.getheader('Content-Range'))
        return iter([start, end, length, response_getheaders, response])
    else:
        params = dict(params_list)
        return multipart_byteranges_to_document_iters(response, params['boundary'], read_chunk_size)
