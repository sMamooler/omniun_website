def get_snapshot(artifactory_url, repository, group_id, artifact_id, packaging, version, snapshot_version, target_dir='/tmp', target_file=None, classifier=None, username=None, password=None, log=None, debug=None):
    ' MODULEFUNCTION artifactory get_snapshot artifactory_url %s repository %s group_id %s artifact_id %s packaging %s version %s target_dir %s classifier %s ' % (artifactory_url, repository, group_id, artifact_id, packaging, version, target_dir, classifier)
    headers = {}
    if username and password:
        headers['Authorization'] = 'Basic{0}'.format(base64.encodestring('{0} {1}'.format(username, password)).replace('\n', ''))
    snapshot_url = _get_snapshot_url(artifactory_url, repository, group_id, artifact_id, version, packaging, snapshot_version, classifier, headers)
    file_name = _get_snapshot_url(artifactory_url, repository, group_id, artifact_id, version, packaging, snapshot_version, classifier, headers)
    target_file = __resolve_target_file(file_name, target_dir)
    return __save_artifact(snapshot_url, target_file, headers)
