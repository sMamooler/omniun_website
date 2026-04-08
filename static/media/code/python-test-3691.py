def preprocess_on_cluster(sff_fps, log_fp, fasta_fp, out_fp='/tmp/', squeeze=False, verbose=False, primer=STANDARD_BACTERIAL_PRIMER):
    cmd = 'denoiser_preprocess py-i%s-l%s-o%s' % (' ', ' '.join(sff_fps), log_fp, out_fp)
    if fasta_fp:
        cmd += '-f%s' % fasta_fp
    if squeeze:
        cmd += '-s'
    if verbose:
        cmd += '-v'
    if primer:
        cmd += '-p%s' % primer
    submit_jobs([cmd], 'pp_' + make_tmp_name(6))
    wait_for_file(out_fp + '/prefix_mapping.txt', 10)
