from dotenv import load_dotenv

load_dotenv()
from flask import Flask, session, request, render_template
from core.config import APP_SECRET_KEY, LLM_MODEL
from extensions import socketio

from livekit import api
import os
from werkzeug.utils import secure_filename
import datetime

from openai import OpenAI

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
app.config["TEMPLATES_AUTO_RELOAD"] = True

socketio.init_app(app)

        


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/api/agent/auth", methods=["GET"])
def get_token():
    timestamp = datetime.datetime.now().strftime("%y%m%d%H%M")
    if "user_id" not in session:
        import uuid

        user_id = f"anon-{uuid.uuid4().hex[:5]}"
        user_name = "Anonymous"
    else:
        user_id = session["user_id"]
        user_name = session["user_name"]
    token = (
        api.AccessToken(os.getenv("LIVEKIT_API_KEY"), os.getenv("LIVEKIT_API_SECRET"))
        .with_identity(f"ricoapp-user-{user_id}")
        .with_name(secure_filename(user_name))
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=f"ricoapp-{timestamp}-{user_id}",
                can_update_own_metadata=True,
                room_record=True,
            )
        )
    )

    auth_data = {
        "url": f"{os.getenv('LIVEKIT_URL')}",
        "token": token.to_jwt(),
        "room": f"ricoapp-{timestamp}-{user_id}",
        "identity": f"ricoapp-user-{user_id}",
    }

    return auth_data

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)
