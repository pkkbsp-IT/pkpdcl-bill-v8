def find_logo():
    candidates = []
    try:
        app = App.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            candidates.append(os.path.join(app.user_data_dir, "pkpdcl_logo.png"))
    except Exception:
        pass
    try:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pkpdcl_logo.png"))
    except Exception:
        pass
    candidates.extend([
        os.path.join(os.getcwd(), "pkpdcl_logo.png"),
        "/storage/emulated/0/Download/PKPDCL/pkpdcl_logo.png",
        "/storage/emulated/0/Download/pkpdcl_logo.png",
        "/storage/emulated/0/Pictures/pkpdcl_logo.png",
    ])
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
            return candidate
    return None
