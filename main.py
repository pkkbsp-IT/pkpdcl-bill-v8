def find_logo():
    candidates = []

    try:
        app = App.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            candidates.append(os.path.join(app.user_data_dir, "pkpdcl_logo.png"))
    except Exception:
        pass

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if base_dir:
            candidates.append(os.path.join(base_dir, "pkpdcl_logo.png"))
    except Exception:
        pass

    try:
        cwd = os.getcwd()
        if cwd:
            candidates.append(os.path.join(cwd, "pkpdcl_logo.png"))
    except Exception:
        pass

    candidates.extend([
        "/storage/emulated/0/Download/PKPDCL/pkpdcl_logo.png",
        "/storage/emulated/0/Download/pkpdcl_logo.png",
        "/storage/emulated/0/Pictures/PKPDCL/pkpdcl_logo.png",
        "/storage/emulated/0/Pictures/pkpdcl_logo.png",
        "/storage/emulated/0/DCIM/PKPDCL/pkpdcl_logo.png",
    ])

    checked = set()
    for path in candidates:
        if not path or path in checked:
            continue
        checked.add(path)
        try:
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                return path
        except Exception:
            continue

    return None
