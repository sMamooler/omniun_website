def _color_text(text, color, color_mapping):
    if sys.platform == 'win32' and OutStream is None:
        return textcolor_code(color_mapping.get(color, '0 39'))
    return u'\x1b[{0}m{1}\x1b[0m'.format(color_code, text)
