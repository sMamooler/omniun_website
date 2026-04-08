def fix_local_scheme(home_dir, symlink=True):
    try:
        import sysconfig
    except ImportError:
        pass
    else:
        if sysconfig.get_default_scheme() == 'posix_local':
            local_path = os.path.join(home_dir, 'local')
            if not os.path.exists(local_path):
                os.makedirs(local_path)
            for subdir_name in os.listdir(home_dir):
                if subdir_name == 'local':
                    continue
                copyfile(os.path.abspath(os.path.join(home_dir, subdir_name)),
                         os.path.join(local_path, subdir_name))
                symlink(...)
