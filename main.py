from threading import Thread

from mitmproxy.http import HTTPFlow 
from fata import web, Shield


# automatically start web interface on separate Thread
Thread(target=web.start_web_interface, daemon=True).start()

# fata engine
shield = Shield(optimize=True, debug=True)

def request(flow: HTTPFlow):
    shield.logger.debug(f"inspecting request for {flow.request.pretty_url}")
    shield.analyze(flow)

def response(flow: HTTPFlow) -> None:
    shield.logger.debug(f"inspecting response for {flow.request.pretty_url}")
    shield.analyze(flow)
