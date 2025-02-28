import ldclient
import os
from ldclient import Context
from ldclient.config import Config
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from weather import get_current_weather
from waitress import serve
from dotenv import load_dotenv
from threading import Lock, Event

load_dotenv()

# set LD sdk_key to use env variable
sdk_key = os.getenv("LD_API_KEY")

feature_flag_key = "wind_speeds"

ldclient.set_config(Config(sdk_key))

client = ldclient.get()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
connected_clients = set()

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/weather')
def get_weather():
    city = request.args.get('city')

    # Check for empty string or strings with only spaces, return default Seattle
    if not bool(city.strip()):
        city = "Seattle"

    weather_data = get_current_weather(city)

    # Handle 404 City Not Found by API
    if not weather_data['cod'] == 200:
        return render_template('city-not-found.html')

    context = Context.builder('bpiper').kind('user').name('Billie Piper').set('email', 'bpiper@wolfcorp.com').build()

    flag_value = client.variation("wind_speeds", context, False)

    if flag_value == True:
        return render_template(
            "winds.html",
            title=weather_data["name"],
            status=weather_data["weather"][0]["description"].capitalize(),
            temp=f"{weather_data['main']['temp']:.1f}",
            feels_like=f"{weather_data['main']['feels_like']:.1f}",
            wind=f"{weather_data['wind']['speed']:.1f}"
        )
    else:
        return render_template(
            "weather.html",
            title=weather_data["name"],
            status=weather_data["weather"][0]["description"].capitalize(),
            temp=f"{weather_data['main']['temp']:.1f}"
        )

@socketio.on('connect')
def handle_connect():
    connected_clients.add(request.sid)
    print(f"Client connected: {request.sid}, Total clients: {len(connected_clients)}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_clients:
        connected_clients.remove(request.sid)
    print(f"Client disconnected: {request.sid}, Total clients: {len(connected_clients)}")

def show_evaluation_result(key: str, value: bool):
    print()
    print(f"*** The {key} feature flag evaluates to {value}")

class FlagValueChangeListener:
    def __init__(self):
        self.__get_weather = True
        self.__lock = Lock()

    def flag_value_change_listener(self, flag_change):
        with self.__lock:
            if self.__get_weather and flag_change.new_value:
                self.__get_weather = False

            show_evaluation_result(flag_change.key, flag_change.new_value)
            
            # Emit the flag change event to all connected clients
            print(f"Broadcasting flag change: {flag_change.key} = {flag_change.new_value}")
            socketio.emit('flag_change', {
                'key': flag_change.key,
                'value': flag_change.new_value
            })


if __name__ == "__main__":
    context = Context.builder('bpiper').kind('user').name('Billie Piper').set('email', 'bpiper@wolfcorp.com').build()
    
    # Initial flag value
    flag_value = ldclient.get().variation(feature_flag_key, context, False)
    show_evaluation_result(feature_flag_key, flag_value)

    # Set up flag change listener
    change_listener = FlagValueChangeListener()
    listener = ldclient.get().flag_tracker.add_flag_value_change_listener(
        feature_flag_key, 
        context, 
        change_listener.flag_value_change_listener
    )

    # Run the server with SocketIO instead of waitress
    socketio.run(app, host="0.0.0.0", port=8000, debug=True, allow_unsafe_werkzeug=True)
