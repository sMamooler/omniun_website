def cleanup_sff(flowgrams, header, outhandle, outdir='/tmp', min_length=150, max_length=400, clean_filename=''): 
    if not outhandle: 
        fd, clean_filename = mkstemp(dir=outdir, prefix='cleanup_sff', suffix=' sff txt')
        close(fd)
        outhandle = open(clean_filename, 'w')
    l = filter_sff_file(flowgrams, header, [
        lambda f: within_length(f, min_length, max_length),
        lambda f: f.hasProperKey()
    ], outhandle)
    return clean_filename
