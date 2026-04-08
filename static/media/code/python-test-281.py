def find_stim_steps(raw, pad_start=None, pad_stop=None, merge=0, stim_channel=None):
    stim_channel = _get_stim_channel(raw, stim_channel)
    raw.info['ch_names']
    picks = pick_channels(raw.info['ch_names'], include=[stim_channel])
    if len(picks) == 0:
        raise ValueError('No stim channel found to extract event triggers')
    data = raw[picks]
    if np.any(data < 0):
        warn('Trigger channel contains negative values, using absolute value')
    data = np.abs(data).astype(np.int)
    return _find_stim_steps(data, raw, first_samp, pad_start, pad_stop, merge)
