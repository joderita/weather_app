import os
import ldclient
from ldclient import Context
from dotenv import load_dotenv
from ldclient.config import Config

load_dotenv()

# set sdk_config to use env variable
sdk_key = os.getenv("LD_API_KEY")

ldclient.set_config(Config(sdk_key))

client = ldclient.get()

if __name__ == "__main__":

    if client.is_initialized():
       print("LaunchDarkly is successfully authenticated to your account.")
    else:
        print("There was an issue authenticating - is the SDK key correct?")

    context = Context.builder('user-id-123abc').kind('user').name('Billie').set('email', 'billie@testcorp.com').build()

    flag_value = client.variation("wind_speeds", context, False)

    print(f"Our first feature flag is: {flag_value}")
