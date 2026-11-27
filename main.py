from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window


class PKPDCLRoot(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=15, **kwargs)

        self.title_label = Label(
            text="PKPDCL Bill Calculator",
            font_size="24sp",
            size_hint_y=None,
            height=60,
        )
        self.status_label = Label(
            text="App initialized successfully.\nReady for billing features.",
            font_size="16sp",
            halign="center",
            valign="middle",
        )
        self.status_label.bind(size=self.status_label.setter("text_size"))

        self.test_btn = Button(
            text="Test Action",
            font_size="18sp",
            size_hint_y=None,
            height=60,
        )
        self.test_btn.bind(on_press=self.on_test_click)

        self.add_widget(self.title_label)
        self.add_widget(self.status_label)
        self.add_widget(self.test_btn)

    def on_test_click(self, instance):
        self.status_label.text = "Button working properly on Android!"


class PKPDCLBillApp(App):
    def build(self):
        self.title = "PKPDCL Bill Calculator"
        return PKPDCLRoot()


if __name__ == "__main__":
    PKPDCLBillApp().run()
