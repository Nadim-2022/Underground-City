from flask import Flask, Response
from flask_socketio import SocketIO
import asyncio
from aiortmp import RTMPServer

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return "RTMP Server is Running"

async def run_rtmp_server():
    server = RTMPServer()
    await server.start('0.0.0.0', 1935)  # Listen on all interfaces

@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(run_rtmp_server())
    socketio.run(app, host='0.0.0.0', port=5000)
