import traceback

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView


def save_log(text):
    for path in (
        "/storage/emulated/0/Download/pkpdcl_crash.log",
        "/sdcard/Download/pkpdcl_crash.log",
    ):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(text)
            return path
        except Exception:
            pass
    return None


class DiagApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.09, 0.14, 1)
        try:
            import qrcode
            import fpdf
            from kivy.uix.image import Image

            box = BoxLayout(orientation="vertical", padding=16, spacing=10)
            box.add_widget(
                Label(
                    text="DIAG OK: qrcode, fpdf, Image imported successfully!",
                    color=(0.25, 1.0, 0.55, 1),
                    bold=True,
                )
            )
            return box
        except Exception:
            tb = traceback.format_exc()
            saved = save_log(tb)
            box = BoxLayout(orientation="vertical", padding=12, spacing=8)
            box.add_widget(
                Label(
                    text=f"CRASH CAUGHT ({saved})",
                    color=(1.0, 0.35, 0.35, 1),
                    bold=True,
                    size_hint_y=None,
                    height=36,
                )
            )
            sv = ScrollView()
            lbl = Label(
                text=tb,
                color=(1, 1, 1, 1),
                size_hint_y=None,
                halign="left",
                valign="top",
            )
            lbl.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1] + 20))
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val - 20, None)))
            sv.add_widget(lbl)
            box.add_widget(sv)
            return box


if __name__ == "__main__":
    DiagApp().run()
