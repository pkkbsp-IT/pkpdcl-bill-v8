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

    found = None
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
            found = candidate
            break

    if not found:
        return None

    try:
        from PIL import Image as PILImage

        with PILImage.open(found) as im:
            if im.mode in ("RGBA", "LA", "P"):
                rgba = im.convert("RGBA")
                bg = PILImage.new("RGB", rgba.size, (255, 255, 255))
                bg.paste(rgba, mask=rgba.split()[-1])
                rgb_img = bg
            else:
                rgb_img = im.convert("RGB")

            out_dir = os.path.dirname(os.path.abspath(found)) or "/tmp"
            out_path = os.path.join(out_dir, "_pkpdcl_logo_clean.png")
            rgb_img.save(out_path, format="PNG")
            if os.path.isfile(out_path) and os.path.getsize(out_path) > 0:
                return out_path
    except Exception:
        pass

    return found
