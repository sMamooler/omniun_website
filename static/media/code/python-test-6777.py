def tokenize(source, may_divide, pos, lineno, end):
    while pos < end:
        for token_type, rule in rules:
            match = rule.match(source, pos)
            if match is not None:
                break
        else:
            if may_divide:
                match = division_re.match(source, pos)
                if match is not None:
                    token_type = 'operator'
            else:
                match = regex_re.match(source, pos)
                if match is not None:
                    token_type = 'regexp'
            if match is None:
                pos += 1
                continue
        token_value = match.group()
        if token_type is not None:
            token = Token(token_type, token_value, lineno, may_divide, indicates_division)
            yield token
            lineno += len(line_re.findall(token_value))
            pos = match.end()
