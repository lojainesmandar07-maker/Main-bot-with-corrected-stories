import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from core.bot import StoryBot
from core.config import DISCORD_TOKEN


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        return


def _start_health_server(port: int) -> None:
    server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    print(f"Health server listening on 0.0.0.0:{port}")
    server.serve_forever()


def main() -> None:
    print("Booting Discord bot service...")
    if not DISCORD_TOKEN:
        raise RuntimeError(
            "Discord token is missing. Set one of: DISCORD_TOKEN, BOT_TOKEN, TOKEN, DISCORD_BOT_TOKEN, TOKEN_BOT."
        )

    # Render Web Services require a bound port; Render Workers do not.
    # Start health server only when a PORT is explicitly provided.
    port_value = os.getenv("PORT")
    if port_value:
        port = int(port_value)
        print(f"Detected Render PORT={port}; starting health server thread.")
        server_thread = threading.Thread(target=_start_health_server, args=(port,), daemon=True)
        server_thread.start()

    bot = StoryBot()
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Bot crashed: {e}")
        print("Sleeping for 60 seconds to prevent rapid restart loop and rate limits...")
        time.sleep(60)
        raise e


if __name__ == "__main__":
    main()
