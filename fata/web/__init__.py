from fata.web.backend import router


def start_web_interface(port: int = 5000):
    router.app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )
