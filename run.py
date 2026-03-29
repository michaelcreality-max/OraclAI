"""Development entrypoint. Production: `gunicorn -w 4 -b 0.0.0.0:5000 server:app`"""

import os

from server import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, threaded=True)
