def check_dna_chars_bcs(header, mapping_data, errors, has_barcodes, valid_dna_chars, DNASequence, iupac_standard_characters, header_fields_to_check):
    check_indices = []
    if has_barcodes:
        header_fields_to_check.append('BarcodeSequence')
    for curr_field in range(len(header)):
        if header[curr_field] in header_fields_to_check:
            check_indices.append(curr_field)
    correction_ix = 1
    for curr_data in range(len(mapping_data)):
        for curr_ix in check_indices:
            if len(mapping_data[curr_data][curr_ix]) == 0:
                errors.append(f'Missing expected DNA sequence DCTB {curr_data} {correction_ix}')
                continue
            for curr_nt in mapping_data[curr_data][curr_ix]:
                if curr_nt not in valid_dna_chars:
                    errors.append(f'Invalid DNA sequence detected {mapping_data[curr_data][curr_ix]} DCTB {curr_data} {correction_ix}')
                    continue
    return errors
