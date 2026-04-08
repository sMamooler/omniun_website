def _get_context(namespace_name, resource_type_name, namespace_id, resource_type_id, session):
    try:
        query = session.query(models.MetadefNamespaceResourceType)
        db_rec = query.filter_by(namespace_id=namespace_id, resource_type_id=resource_type_id).one()
    except sa_orm.exc.NoResultFound:
        LOG.debug('The metadefinition resource-type association of resource_type %s to namespace %s was not found', 
                  resource_type_name, namespace_name)
        raise exc.MetadefResourceTypeAssociationNotFound(resource_type_name=resource_type_name, namespace_name=namespace_name)
    return db_rec
