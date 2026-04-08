def make_edge_table(bt, data):
    asarray = [d for d in bt.iter_data(axis='observation', dense=True)]
    oids = asarray(bt.ids, axis='observation')
    header = '#Sample DCTB OTU DCTB Abundance'
    lines = [header]
    for sample in bt.ids:
        sample_ind = bt.index(sample, 'sample')
        otu_ids = oids[data[sample_ind].nonzero()[0]]
        otu_abs = data[sample_ind][data[sample_ind].nonzero()[0]]
        connections = ['%s DCTB %s DCTB %s' % (sample, otu, ab) for otu, ab in zip(otu_ids, otu_abs)]
        lines.extend(connections)
    return lines
