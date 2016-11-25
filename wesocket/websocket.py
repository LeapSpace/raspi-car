#!/usr/bin/env python

import io
import os
from subprocess import Popen, PIPE
from struct import Struct
from threading import Thread
from time import sleep, time
from wsgiref.simple_server import make_server

import picamera
from ws4py.websocket import WebSocket
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication

###########################################
# CONFIGURATION
WIDTH = 640
HEIGHT = 480
FRAMERATE = 24
WS_PORT = 8084
COLOR = u'#444'
BGCOLOR = u'#333'
JSMPEG_MAGIC = b'jsmp'
JSMPEG_HEADER = Struct('>4sHH')
###########################################


class StreamingWebSocket(WebSocket):
	def opened(self):
		self.send(JSMPEG_HEADER.pack(JSMPEG_MAGIC, WIDTH, HEIGHT), binary=True)


class BroadcastOutput(object):
	def __init__(self, camera):
		print('Spawning background conversion process')
		self.converter = Popen([
			'avconv',
			'-f', 'video4linux2',
			'-pix_fmt', 'yuv420p',
			'-s', '%dx%d' % camera.resolution,
			'-r', str(float(camera.framerate)),
			'-i', '/dev/video0',
			'-f', 'mpeg1video',
			'-b', '800k',
			'-r', str(float(camera.framerate)),
			'-'],
			stdin=PIPE, stdout=PIPE, stderr=io.open(os.devnull, 'wb'),
			shell=True, close_fds=True)

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
			i=0
			while True:
				buf = self.converter.stdout.read(512)
				if buf:
					self.websocket_server.manager.broadcast(buf, binary=True)
				elif self.converter.poll() is not None:
					break
				else:
					continue
		except Exception as e:
			raise e
		finally:
			self.converter.stdout.close()


def main():
	print('Initializing camera')
	with picamera.PiCamera() as camera:
		camera.resolution = (WIDTH, HEIGHT)
		camera.framerate = FRAMERATE
		sleep(1) # camera warm-up time
		print('Initializing websockets server on port %d' % WS_PORT)
		websocket_server = make_server(
			'', WS_PORT,
			server_class=WSGIServer,
			handler_class=WebSocketWSGIRequestHandler,
			app=WebSocketWSGIApplication(handler_cls=StreamingWebSocket))
		websocket_server.initialize_websockets_manager()
		websocket_thread = Thread(target=websocket_server.serve_forever)
		output = BroadcastOutput(camera)
		broadcast_thread = BroadcastThread(output.converter, websocket_server)
		print('Starting recording')
		camera.start_recording(output, 'yuv')
		try:
			print('Starting websockets thread')
			websocket_thread.start()
			print('Starting broadcast thread')
			broadcast_thread.start()
			while True:
				camera.wait_recording(1)
		except KeyboardInterrupt:
			pass
		except Exception as e:
			raise e
		finally:
			print('Stopping recording')
			camera.stop_recording()
			print('Waiting for broadcast thread to finish')
			broadcast_thread.join()
			print('Shutting down websockets server')
			websocket_server.shutdown()
			print('Waiting for websockets thread to finish')
			websocket_thread.join()


if __name__ == '__main__':
	main()
