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

@app.route('/api/randint32')
def randint32():
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

@app.route('/api/randuniform')
def randuniform():
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

@app.route('/api/randnormal')
def randnormal():
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

@app.route('/api/randhex')
def randhex():
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

@app.errorhandler(Exception)
def handle_exception(e):
    return Response(e.description, status=e.code, content_type='text/plain')

server = pywsgi.WSGIServer(('0.0.0.0', 62456), application=app, handler_class=WebSocketHandler)
server.serve_forever()
