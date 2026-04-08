def crawl(links, domains, delay, parse, sort, method, DEPTH, **kwargs):
    crawler = Crawler(links, domains, delay, parse, sort, method, DEPTH, **kwargs)
    crawler.bind('visit', lambda crawler, link, source: None)
    setattr(crawler, 'crawled', lambda link, source: None)
    while not crawler.done:
        crawler.crawled(None, None)
        crawler.crawl(method, **kwargs)
    yield crawler.crawled
