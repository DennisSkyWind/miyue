#!/usr/bin/env python3
import os, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread

html_path = '/home/ubuntu/miyue/电子书/video_chapters/chapter7/html/chapter7.html'
html_dir = os.path.dirname(os.path.abspath(html_path))
os.chdir(html_dir)
print(f'CWD: {os.getcwd()}')
print(f'HTML exists: {os.path.exists(os.path.basename(html_path))}')

server = HTTPServer(('127.0.0.1', 0), SimpleHTTPRequestHandler)
t = Thread(target=server.serve_forever, daemon=True)
t.start()
port = server.server_address[1]
print(f'Server port: {port}')
time.sleep(2)
print('Server alive, shutting down...')
server.shutdown()
print('Done')
