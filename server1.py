import os
import ldclient
from ldclient import Context
from ldclient.config import Config
from threading import Lock, Event
from flask import Flask, render_template, request
from weather import get_current_weather
from waitress import serve

# Set sdk_key to look for LaunchDarkly SDK key in env variables
sdk_key = os.getenv("LD_API_KEY")

# Set feature flag to Wind Speeds feature
feature_flag_key = "wind_speeds"

# Print the flag value to show that it is working dynamically
def show_evaluation_result(key: str, value: bool):
    print()
    print(f"***The {key} feature flag evaluates to {value}")

app = Flask(__name__)

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

    return render_template(
        "weather.html",
        title=weather_data["name"],
        status=weather_data["weather"][0]["description"].capitalize(),
        temp=f"{weather_data['main']['temp']:.1f}"
    )


def get_wind():
    city = request.args.get('city')

    # Check for empty string or strings with only spaces, return default Surprise
    if not bool(city.strip()):
        city = "Surprise"

    wind_data = get_current_weather(city)

    if not wind_data['cod'] == 200:
        return render_template('city-not-found.html')

    return render_template(
        "winds.html",
        title=wind_data["name"],
        status=wind_data["weather"][0]["description"].capitalize(),
        temp=f"{wind_data['main']['temp']:.1f}",
        wind=f"{wind_data['wind']['speed']:.1f}",
        feels_like=f"{wind_data['main']['feels_like']:.1f}"
    ) 


class FlagValueChangeListener:
    def __init__(self):
        self.__get_wind = True
        self.__lock = Lock()

    def flag_value_change_listener(self, flag_change):
        with self.__lock:
            if self.__get_wind and flag_change.new_value:
                get_wind()
                slef.__get_wind = False
            show_evaluation_result(flag_change.key, flag_change.new_value)


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8000)

    ldclient.set_config(Config(sdk_key))

    if not ldclient.get().is_initialized():
        print("*** SDK failed to initialize. Please check your SDK credential for typos.")
        exit()

    context = Context.builder('bpiper').kind('user').name('Billie Piper').build()

    flag_value = ldclient.get().variation(feature_flag_key, context, False)
    show_evaluation_result(feature_flag_key, flag_value)

    change_listener = FlagValueChangeListener()
    listener = ldclient.get().flag_tracker \
        .add_flag_value_change_listener(feature_flag_key, context, change_listener.flag_value_change_listener)

    try:
        Event().wait()
    except KeyboardInterrupt:
        pass
