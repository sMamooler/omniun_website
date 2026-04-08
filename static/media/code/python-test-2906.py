def _require_valid_version(version_from_payload, exploration_version):
    if version_from_payload is None:
        raise base.BaseHandler.InvalidInputException('Invalid POST request: a version must be specified')
    if version_from_payload < exploration_version:
        raise base.BaseHandler.InvalidInputException('Trying to update version %s of exploration from version %s which is too old. Please reload the page and try again.' % (exploration_version, version_from_payload))
