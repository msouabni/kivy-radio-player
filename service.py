'p4a example service using oscpy to communicate with main application.'
from time import sleep

from oscpy.server import OSCThreadServer
from oscpy.client import OSCClient
from jnius import autoclass, JavaException
MediaPlayer = autoclass("android.media.MediaPlayer")
FileInputStream = autoclass("java.io.FileInputStream")
AudioManager = autoclass("android.media.AudioManager")


CLIENT = OSCClient('localhost', 3002)
new_counter = 0
counter = -1
APP_STATUS = 'running'
player = MediaPlayer()
stream_to_play = None
service_status = 'free'




def play(stream):
    # global player
    # player.stop()
    # player.release()
    # player = None
    # player = MediaPlayer()
    # # player.reset()
    # # player.setDataSource('http://s8-webradio.antenne.de/chillout')
    # player.setDataSource(stream.decode('utf8'))
    # player.setAudioStreamType(AudioManager.STREAM_NOTIFICATION)
    # player.prepare()
    # player.start()
    # player = RadioSoundLoader.load(stream.decode('utf8'))
    # player.play()
    global stream_to_play
    stream_to_play = stream.decode('utf8')


def play_streaming():
    global player
    global stream_to_play
    global service_status

    if player and stream_to_play == 'pause':
        if player.isPlaying():
            player.stop()
            player.reset()
            stream_to_play = None
            service_status = 'free'

    elif player and stream_to_play:

        current_stream_to_play = stream_to_play
        service_status = 'loading'

        if player.isPlaying():
            player.stop()

        player.reset()
        player.setDataSource(stream_to_play)
        player.setAudioStreamType(AudioManager.STREAM_NOTIFICATION)
        CLIENT.send_message(b'/log',
                            [
                                'Trying to load {}'.format(stream_to_play).encode('utf8'),
                            ], )
        try:
            player.prepare()
            player.start()
            service_status = 'playing'
        except JavaException as e:
            CLIENT.send_message(b'/log',
                [
                    'Error during loading {}'.format(e).encode('utf8'),
                ], )

            player.reset()
            service_status = 'free'
        if current_stream_to_play == stream_to_play:
            stream_to_play = None



def ping(*_):
    'answer to ping messages'
    global new_counter
    global service_status
    new_counter += 1
    # SERVER.answer(b'/pong', values=[service_status.encode('utf8')])
    CLIENT.send_message(
        b'/pong',
        [
            service_status.encode('utf8'),
        ],
    )
    # CLIENT.send_message(
    #     b'/message',
    #     [
    #         str(new_counter).encode('utf8'),
    #     ],
    # )

# def test_alive(message):
#     return message

def set_app_status(status):
    global APP_STATUS
    APP_STATUS = status.decode('utf8')
    if APP_STATUS == 'running':
        new_counter = 0
        counter = -1


def pause():
    global stream_to_play
    stream_to_play = 'pause'


if __name__ == '__main__':
    SERVER = OSCThreadServer()
    SERVER.listen('localhost', port=3000, default=True)
    SERVER.bind(b'/ping', ping)
    SERVER.bind(b'/app_status', set_app_status)
    SERVER.bind(b'/play', play)
    SERVER.bind(b'/pause', pause)
    #RadioSoundLoader.load('https://radio.mosaiquefm.net/mosalive')
    while new_counter > counter or APP_STATUS == 'paused' :
        counter = new_counter
        play_streaming()
        # if counter == -1:
        #     sleep(5)
        # else:
        #     sleep(2)
        sleep(1)
        #send_date()
