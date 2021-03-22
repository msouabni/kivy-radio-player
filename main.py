# import os
# os.environ['KIVY_AUDIO'] = 'ffpyplayer'

from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage, Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.core.audio import SoundLoader
#from kivy.core.audio.audio_ffpyplayer import SoundLoader
#from kivy.core.audio.audio_gstplayer import SoundGstplayer
from kivy.resources import resource_find
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
import urllib.request
from kivy.utils import platform
from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer
from jnius import autoclass
from kivy.base import stopTouchApp
from kivy.clock import Clock

# MediaPlayer = autoclass("android.media.MediaPlayer")
# FileInputStream = autoclass("java.io.FileInputStream")
# AudioManager = autoclass("android.media.AudioManager")
# player=MediaPlayer()
# player.setAudioStreamType(AudioManager.STREAM_MUSIC)
# player.setDataSource('http://s8-webradio.antenne.de/chillout')
# # player.setAudioStreamType(AudioManager.STREAM_NOTIFICATION)
# player.prepare()
# player.start()

import json

SERVICE_NAME = u'{packagename}.Service{servicename}'.format(
    packagename=u'org.kivyradio.kivyradio',
    servicename=u'Radioplayer'
)

with open("radio_stations.json") as f:
    data = f.read()

radio_stations = json.loads(data)


class Config():
    LOGO_W = 232
    LOGO_H = 232
    LOGO_X_MARGIN = 15
    LOGO_Y_MARGIN = 15
    PLAYER_CONTAINER_H = 100
    CAROUSEL_CONTROLS_H = 48

# class RadioSoundLoader(SoundLoader):
#     @staticmethod
#     def load(filename):
#         '''Load a sound, and return a Sound() instance.'''
#         rfn = resource_find(filename)
#         if rfn is not None:
#             filename = rfn
#         ext = filename.split('.')[-1].lower()
#         if '?' in ext:
#             ext = ext.split('?')[0]
#         for classobj in SoundLoader._classes:
#             c = classobj(source=filename)
#             return c
#         Logger.warning('Audio: Unable to find a loader for <%s>' %
#                        filename)
#         return None


class RadioStationButton(ButtonBehavior, AsyncImage):

    def __init__(self, radio_id, *args, **kwargs):
        self.radio_id = radio_id
        super(RadioStationButton, self).__init__(*args, **kwargs)

    def on_press(self):
        app = App.get_running_app()
        app.current_logo = radio_stations[self.radio_id]['logo']
        stream = radio_stations[self.radio_id]['streamings']
        app.current_stream = stream
        app.play(stream)


class CarouselNavItem(ButtonBehavior, Image):

    def __init__(self, slide_id, *args, **kwargs):
        self.slide_id = slide_id
        super(CarouselNavItem, self).__init__(*args, **kwargs)

    def on_press(self):
        app = App.get_running_app()
        app.root.ids.carousel.index = self.slide_id


class AppLayout(BoxLayout):

    def update_carousel_nav(self):
        for i in range(len(self.ids.carousel_nav.items)):
            if i == self.ids.carousel.index:
                self.ids.carousel_nav.items[i].source = 'data/cercle_w.png'
            else:
                self.ids.carousel_nav.items[i].source = 'data/cercle_g.png'

    def generate_carousel(self):
        width = Window.size[0]
        height = Window.size[1] - Config.CAROUSEL_CONTROLS_H - Config.PLAYER_CONTAINER_H
        nb_items_x = int(width / (Config.LOGO_W + 2 * Config.LOGO_X_MARGIN))
        nb_items_y = int(height / (Config.LOGO_H + 2 * Config.LOGO_Y_MARGIN))
        items_per_slider = nb_items_y * nb_items_x
        nb_sliders = int(len(radio_stations) / items_per_slider) + (0 if (len(radio_stations) % items_per_slider == 0) else 1)
        #nb_sliders += 0 if (len(radio_stations) % items_per_slider == 0) else 1
        #print("window", height)
        #print("hello", self.ids.carousel.parent.size)
        #print("nb item x", nb_items_x)
        #print("bn item y", nb_items_y)
        #print("nb of radios", len(radio_stations))
        #print("nb of sliders", nb_sliders)
        grids = []
        cercle_img_file = 'data/cercle_g.png'
        for i in range(nb_sliders):
            #print(i)
            g =GridLayout(cols=nb_items_x, padding=[Config.LOGO_X_MARGIN, Config.LOGO_Y_MARGIN,Config.LOGO_X_MARGIN, Config.LOGO_Y_MARGIN], spacing=Config.LOGO_X_MARGIN)
            limit = min((i+1) * items_per_slider, len(radio_stations))
            for j in range(i * items_per_slider, limit):
                #print(j)
                #print(radio_stations[j])
                #g.add_widget(AsyncImage(source=radio_stations[j]["logo"]))
                g.add_widget(RadioStationButton(radio_id=j, source=radio_stations[j]["logo"], allow_stretch=True))
            grids.append(g)

        i = 0
        self.ids.carousel_nav.items = []
        for g in grids:
            if i == 0:
                cercle_img_file = 'data/cercle_w.png'
            else:
                cercle_img_file = 'data/cercle_g.png'
            nav_item = CarouselNavItem(source=cercle_img_file, slide_id=i)
            self.ids.carousel_nav.items.append(nav_item)
            self.ids.carousel_nav.add_widget(nav_item)
            self.ids.carousel.add_widget(g)
            i += 1

        # generate AsyncImages

    def close_app(self):
        app = App.get_running_app()
        app.stop()
        app.stop_service()
        Window.close()


class MainApp(App):
    current_logo = StringProperty(defaultvalue='http://tunisiefm.net/sites/default/files/styles/medium_2/public/radio/logos/logo-jawhara-fm_1.png?itok=KGeCDSH4')
    current_stream = StringProperty(defaultvalue=None)
    def __init__(self, *args, **kwargs):
        self.uiDict = {}
        self.cfg = Config()
        #self.t = 48
        super(MainApp, self).__init__(*args, **kwargs)
    # def stop(self, *largs):
    #     self.root_window.close() # Fix app exit on Android.
    #     return super(MainApp, self).stop(*largs)

    def pause(self):
        self.client.send_message(b'/pause', [])

    def play(self, stream):
        self.client.send_message(b'/play', [stream.encode('utf8')])

    def close_app(self):
        # self.root_window.close()  # Fix app exit on Android.
        stopTouchApp()
        # App.get_running_app().stop()
        # Window.close()

    def on_stop(self):
        Logger.critical("Stopping")
        self.stop_service()
        return True

    def check_service(self, *lars):
        self.client.send_message(b'/ping', [])

    def on_pause(self):
        self.client.send_message(b'/app_status', ['paused'.encode('utf8')])
        return True

    def on_resume(self):
        self.client.send_message(b'/app_status', ['running'.encode('utf8')])

    def build(self):
        self.service = None
        self.start_service()

        self.server = server = OSCThreadServer()
        Clock.schedule_interval(self.check_service,1)
        server.listen(
            address=b'localhost',
            port=3002,
            default=True,
        )

        server.bind(b'/message', self.display_message)
        server.bind(b'/date', self.date)
        server.bind(b'/pong', self.pong)
        server.bind(b'/log', self.log)
        # server.bind(b'/alive', self.alive)

        self.client = OSCClient(b'localhost', 3000)
        self.root = AppLayout()
        return self.root

    def start_service(self):
        if platform == 'android':
            service = autoclass(SERVICE_NAME)
            self.mActivity = autoclass(u'org.kivy.android.PythonActivity').mActivity
            argument = 'true'
            service.start(self.mActivity, argument)
            self.service = service

        elif platform in ('linux', 'linux2', 'macos', 'win'):
            from runpy import run_path
            from threading import Thread
            self.service = Thread(
                target=run_path,
                args=['src/service.py'],
                kwargs={'run_name': '__main__'},
                daemon=True
            )
            self.service.start()
        else:
            raise NotImplementedError(
                "service start not implemented on this platform"
            )

    def stop_service(self):
        if self.service:
            if platform == 'android':
                self.service.stop(self.mActivity)
            else:
                self.service.stop()
            self.service = None

    def send(self, *args):
        self.client.send_message(b'/ping', [])

    def display_message(self, message):
        if self.root:
            self.root.ids.radio_title.text = '{}\n'.format(message.decode('utf8'))

    def pong(self, status):
        if self.root:
            self.root.ids.pstatus.text = status.decode('utf8')

    def date(self, message):
        # self.client.send_message(b'alive')
        if self.root:
            self.root.ids.date.text = message.decode('utf8')

    def change_logo(self):
        self.current_logo = 'http://tunisiefm.net/sites/default/files/styles/medium_2/public/radio/logos/logo-mwzyk-fm.jpg?itok=cesEGUX_'

    def resume(self):
        self.play(self.current_stream)

    def log(self, message):
        Logger.info('RadioPlayer Service : {}'.format(message.decode('utf8')))

if __name__ == '__main__':
    MainApp().run()