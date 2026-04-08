def quickstart_generator(war_path, sdk_root=None):
    if not sdk_root:
        sdk_root = _SDK_ROOT
    quickstart_xml_path = os.path.join(war_path, 'WEB-INF', 'quickstart-web xml')
    if os.path.exists(quickstart_xml_path):
        os.remove(quickstart_xml_path)
    java_home, exec_suffix = java_utils.JavaHomeAndSuffix()
    java_command = os.path.join(java_home, 'bin', 'java') + exec_suffix
    quickstartgenerator_jar = os.path.join(sdk_root, _QUICKSTART_JAR_PATH)
    webdefaultxml = os.path.join(sdk_root, _JAVA_VMRUNTIME_PATH, 'etc', 'webdefault xml')
    command = [java_command, '-jar', quickstartgenerator_jar, war_path, webdefaultxml]
    subprocess.check_call(command)
    with open(quickstart_xml_path) as f:
        return f.read()
