"""Start the server with:  python app.py"""

import os

from budgetmate import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True reloads on code changes. Never use it on a public server.
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=True,
    )
