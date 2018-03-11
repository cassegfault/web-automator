def force_utf8(s):
    if not isinstance(s, basestring):
        return s
    try:
        s = s.decode('utf-8', 'replace')
    except UnicodeEncodeError:
        s = s.encode('utf-8', 'replace')
        s = s.decode('utf-8', 'replace')

    return s.encode('utf-8', 'ignore').strip()