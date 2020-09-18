# Copyright (c) 2020 Andika Wasisto
# Modified by Tobias Raayoni Last
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import threading
import json

from flask import Flask, request, Response
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from quanttp.data.qng_wrapper_linux import QngWrapperLinux
from quanttp.data.qng_wrapper_windows import QngWrapperWindows

app = Flask(__name__)
sockets = Sockets(app)

qng_wrapper = QngWrapperWindows() if (os.name == 'nt') else QngWrapperLinux()

# Original API ----------------------------------------------

@app.route('/api/randint32')
def randint32():
    return Response(str(qng_wrapper.randint32()), content_type='text/plain')


@app.route('/api/randuniform')
def randuniform():
    return Response(str(qng_wrapper.randuniform()), content_type='text/plain')


@app.route('/api/randnormal')
def randnormal():
    return Response(str(qng_wrapper.randnormal()), content_type='text/plain')

@app.route('/api/randhex')
def randhex():
    try:
        length = int(request.args.get('length'))
        if length < 1:
            return Response('length must be greater than 0', status=400, content_type='text/plain')
        return Response(qng_wrapper.randbytes(length).hex(), content_type='text/plain')
    except (TypeError, ValueError) as e:
        return Response(str(e), status=400, content_type='text/plain')

@app.route('/api/randbytes')
def randbytes():
    try:
        length = int(request.args.get('length'))
        if length < 1:
            return Response('length must be greater than 0', status=400, content_type='text/plain')
        return Response(qng_wrapper.randbytes(length), content_type='application/octet-stream')
    except (TypeError, ValueError) as e:
        return Response(str(e), status=400, content_type='text/plain')

# JSON API ----------------------------------------------

@app.route('/api/json/randint32')
def randjsonint32():
    try:
        length = int(request.args.get('length'))
        if length < 1:
            return Response('length must be greater than 0', status=400, content_type='text/plain')
        int32array = []
        for x in range(0, length):
            int32array.append(qng_wrapper.randint32())
        return Response(json.dumps({"type": "string", "format": "int32", "length":length, "data": int32array, "success": "true"}), content_type='text/plain')
    except (TypeError, ValueError) as e:
        return Response(json.dumps({"error": str(e), "success":"false"}), status=400, content_type='text/plain')

@app.route('/api/json/randuniform')
def randjsonuniform():
    try:
        length = int(request.args.get('length'))
        if length < 1:
            return Response('length must be greater than 0', status=400, content_type='text/plain')
        uniformarray = []
        for x in range(0, length):
            uniformarray.append(qng_wrapper.randuniform())
        return Response(json.dumps({"type": "string", "format": "uniform", "length":length, "data": uniformarray, "success": "true"}), content_type='text/plain')
    except (TypeError, ValueError) as e:
        return Response(json.dumps({"error": str(e), "success":"false"}), status=400, content_type='text/plain')

@app.route('/api/json/randnormal')
def randjsonnormal():
    try:
        length = int(request.args.get('length'))
        if length < 1:
            return Response('length must be greater than 0', status=400, content_type='text/plain')
        normarray = []
        for x in range(0, length):
            normarray.append(qng_wrapper.randnormal())
        return Response(json.dumps({"type": "string", "format": "normal", "length":length, "data": normarray, "success": "true"}), content_type='text/plain')
    except (TypeError, ValueError) as e:
        return Response(json.dumps({"error": str(e), "success":"false"}), status=400, content_type='text/plain')

@app.route('/api/json/randhex')
def randjsonhex():
    try:
        length = int(request.args.get('length'))
        size = int(request.args.get('size'))
        if length < 1:
            return Response('length must be greater than 0', status=400, content_type='text/plain')
        if size < 1:
            return Response('size must be greater than 0', status=400, content_type='text/plain')
        hexarray = []
        for x in range(0, length):
            hexarray.append(qng_wrapper.randbytes(size).hex())
        return Response(json.dumps({"type": "string", "format": "hex", "length":length, "size": size, "data": hexarray, "success": "true"}), content_type='text/plain')
    except (TypeError, ValueError) as e:
        return Response(json.dumps({"error": str(e), "success":"false"}), status=400, content_type='text/plain')

@app.route('/api/clear')
def clear():
    qng_wrapper.clear()
    return Response(status=204)

# Websockets ----------------------------------------------

@sockets.route('/ws')
def ws(websocket):
    subscribed = [False]
    while not websocket.closed:
        threading.Thread(target=handle_ws_message, args=(websocket.receive(), websocket, subscribed)).start()

def handle_ws_message(message, websocket, subscribed):
    try:
        split_message = message.strip().upper().split()
        if split_message[0] == 'RANDINT32':
            websocket.send(str(qng_wrapper.randint32()))
        elif split_message[0] == 'RANDUNIFORM':
            websocket.send(str(qng_wrapper.randuniform()))
        elif split_message[0] == 'RANDNORMAL':
            websocket.send(str(qng_wrapper.randnormal()))
        elif split_message[0] == 'RANDBYTES':
            length = int(split_message[1])
            if length < 1:
                raise ValueError()
            websocket.send(qng_wrapper.randbytes(length))
        elif split_message[0] == 'SUBSCRIBEINT32':
            if not subscribed[0]:
                subscribed[0] = True
                while subscribed[0] and not websocket.closed:
                    websocket.send(str(qng_wrapper.randint32()))
        elif split_message[0] == 'SUBSCRIBEUNIFORM':
            if not subscribed[0]:
                subscribed[0] = True
                while subscribed[0] and not websocket.closed:
                    websocket.send(str(qng_wrapper.randuniform()))
        elif split_message[0] == 'SUBSCRIBENORMAL':
            if not subscribed[0]:
                subscribed[0] = True
                while subscribed[0] and not websocket.closed:
                    websocket.send(str(qng_wrapper.randnormal()))
        elif split_message[0] == 'SUBSCRIBEBYTES':
            chunk = int(split_message[1])
            if chunk < 1:
                raise ValueError()
            if not subscribed[0]:
                subscribed[0] = True
                while subscribed[0] and not websocket.closed:
                    websocket.send(qng_wrapper.randbytes(chunk))
        elif split_message[0] == 'SUBSCRIBEHEX':
            chunk = int(split_message[1])
            if chunk < 1:
                raise ValueError()
            if not subscribed[0]:
                subscribed[0] = True
                while subscribed[0] and not websocket.closed:
                    websocket.send(qng_wrapper.randbytes(chunk).hex())
        elif split_message[0] == 'UNSUBSCRIBE':
            subscribed[0] = False
            websocket.send('UNSUBSCRIBED')
        elif split_message[0] == 'CLEAR':
            qng_wrapper.clear()
    except (IndexError, ValueError, BlockingIOError):
        pass
    except Exception as e:
        websocket.close(code=1011, message=str(e))

@app.errorhandler(Exception)
def handle_exception(e):
    return Response(e.description, status=e.code, content_type='text/plain')

server = pywsgi.WSGIServer(('0.0.0.0', 62456), application=app, handler_class=WebSocketHandler)
server.serve_forever()
