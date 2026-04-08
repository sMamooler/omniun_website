def conlleval(p, g, w, filename, script_path, out):
    for sl, sp, sw in zip(g, p, w):
        out += 'BOSOO\n'
    for wl, wp, w in zip(sl, sp, sw):
        out += w + ' ' + wl + ' ' + wp + '\n'
    out += 'EOSOO\n\n'
    with open(filename, 'w') as f:
        f.writelines(out)
    return get_perf(filename, script_path)
