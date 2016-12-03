#!/usr/bin/env python

import io
import os
from struct import Struct
from subprocess import PIPE, Popen
from threading import Thread
from time import sleep
from wsgiref.simple_server import make_server

import picamera
from ws4py.server.wsgirefserver import WebSocketWSGIRequestHandler, WSGIServer
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py.websocket import WebSocket


WIDTH = 800
HEIGHT = 608
FRAMERATE = 30
WS_PORT = 8084
JSMPEG_MAGIC = b'jsmp'
JSMPEG_HEADER = Struct('>4sHH')


class StreamingWebSocket(WebSocket):
    def opened(self):
        self.send(JSMPEG_HEADER.pack(JSMPEG_MAGIC, WIDTH, HEIGHT), binary=True)


class BroadcastOutput(object):
    def __init__(self, camera):
        print('Spawning background conversion process')
        self.converter = Popen([
            'avconv',
            '-threads', '1',
            '-f', 'rawvideo',
            '-pix_fmt', 'yuv420p',
            '-s', '%dx%d' % camera.resolution,
            '-r', str(float(camera.framerate)),
            '-i', '-',
            '-f', 'mpeg1video',
            '-b', '1000k',
            '-r', str(float(camera.framerate)),
            '-vf', 'hflip',
            '-'],
            stdin=PIPE, stdout=PIPE, stderr=io.open(os.devnull, 'wb'),
            shell=False, close_fds=True)

    def write(self, b):
        self.converter.stdin.write(b)

    def flush(self):
        print('Waiting for background conversion process to exit')
        self.converter.stdin.close()
        self.converter.wait()


class BroadcastThread(Thread):
    def __init__(self, converter, websocket_server):
        super(BroadcastThread, self).__init__()
        self.converter = converter
        self.websocket_server = websocket_server

    def run(self):
        try:
            while True:
                buf = self.converter.stdout.read(512)
                if buf:
                    self.websocket_server.manager.broadcast(buf, binary=True)
                elif self.converter.poll() is not None:
                    break
        finally:
            self.converter.stdout.close()


def main():
    with picamera.PiCamera() as camera:
        camera.resolution = (WIDTH, HEIGHT)
        camera.framerate = FRAMERATE
        sleep(1)  # camera warm-up time

        websocket_server = make_server(
            '0.0.0.0', WS_PORT,
            server_class=WSGIServer,
            handler_class=WebSocketWSGIRequestHandler,
            app=WebSocketWSGIApplication(handler_cls=StreamingWebSocket))
        websocket_server.initialize_websockets_manager()
        websocket_thread = Thread(target=websocket_server.serve_forever)

        output = BroadcastOutput(camera)
        broadcast_thread = BroadcastThread(output.converter, websocket_server)

        camera.start_recording(output, 'yuv')
        try:
            websocket_thread.start()
            broadcast_thread.start()
            while True:
                camera.wait_recording(1)
        except KeyboardInterrupt:
            pass
        finally:
            camera.stop_recording()
            broadcast_thread.join()
            websocket_server.shutdown()
            websocket_thread.join()


if __name__ == '__main__':
    main()
