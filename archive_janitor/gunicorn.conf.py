# gunicorn.conf.py
def when_ready(server):
    import threading, time
    server.log.info("🐚 Echo awakening under Gunicorn...")

    def _delayed_start():
        time.sleep(3)  # let the app and FAISS initialize
        from run import start_background_threads
        server.log.info("🚀 Starting Echo's background threads...")
        start_background_threads()

    threading.Thread(target=_delayed_start, daemon=True).start()

