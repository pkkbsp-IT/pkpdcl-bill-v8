import traceback

class PKPDCLApp(App):
    def build(self):
        try:
            Window.clearcolor = get_color_from_hex("#EEF3FA")
            base_dir = get_base_dir(self)
            self.store = PKPDCLStore(base_dir)
            sm = ScreenManager()
            sm.add_widget(HomeScreen(self.store, name="home"))
            sm.add_widget(BillScreen(self.store, name="bill"))
            return sm
        except Exception:
            err_text = traceback.format_exc()
            try:
                with open("/sdcard/Download/pkpdcl_crash.log", "w", encoding="utf-8") as f:
                    f.write(err_text)
            except Exception:
                pass
            box = BoxLayout(orientation="vertical", padding=12, spacing=8)
            box.add_widget(
                Label(
                    text="APP STARTUP ERROR",
                    bold=True,
                    color=(1, 0.2, 0.2, 1),
                    size_hint_y=None,
                    height=36,
                )
            )
            scroll = ScrollView()
            lbl = Label(
                text=err_text,
                color=(1, 1, 1, 1),
                size_hint_y=None,
                halign="left",
                valign="top",
            )
            lbl.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1] + 20))
            lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val - 20, None)))
            scroll.add_widget(lbl)
            box.add_widget(scroll)
            return box
