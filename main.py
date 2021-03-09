
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

class AppLayout(BoxLayout):
    pass



class MainApp(App):
    def build(self):
        return AppLayout()


if __name__ == '__main__':
    MainApp().run()