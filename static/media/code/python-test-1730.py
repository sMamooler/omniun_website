def GetXcodeArchsDefault():
    global XCODE_ARCHS_DEFAULT_CACHE
    if XCODE_ARCHS_DEFAULT_CACHE:
        return XCODE_ARCHS_DEFAULT_CACHE
    xcode_version = XcodeVersion()
    if xcode_version < '0500':
        XCODE_ARCHS_DEFAULT_CACHE = XcodeArchsDefault('$ARCHS_STANDARD')
        XcodeArchsVariableMapping(['i386'])
        XcodeArchsVariableMapping(['i386', 'x86_64'])
        XcodeArchsVariableMapping(['armv7', 'armv7s', 'arm64'])
    elif xcode_version < '0510':
        XCODE_ARCHS_DEFAULT_CACHE = XcodeArchsDefault('$ARCHS_STANDARD_INCLUDING_64_BIT')
        XcodeArchsVariableMapping(['x86_64'])
        XcodeArchsVariableMapping(['i386', 'x86_64'])
        XcodeArchsVariableMapping(['armv7', 'armv7s', 'arm64'])
    else:
        XCODE_ARCHS_DEFAULT_CACHE = XcodeArchsDefault('$ARCHS_STANDARD')
        XcodeArchsVariableMapping(['x86_64'])
        XcodeArchsVariableMapping(['i386', 'x86_64'])
        XcodeArchsVariableMapping(['armv7', 'armv7s', 'arm64'])
    return XCODE_ARCHS_DEFAULT_CACHE
