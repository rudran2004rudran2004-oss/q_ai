"""
lmstudio_server.py  –  standalone LM Studio chat backend (with streaming)
Runs on port 5001. Your main Flask app proxies to it via /assistant.

LM Studio must be running with the local server enabled at:
    http://192.168.56.1:1234

Install:
    pip install flask flask-cors requests
"""

import os
import json
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ── Configure LM Studio ───────────────────────────────────────────────────────
LM_STUDIO_BASE_URL = "http://192.168.56.1:1234/v1"

SYSTEM_PROMPT = (
    "You are a helpful, friendly assistant. "
    "Answer clearly and concisely. Use markdown formatting when it helps readability."
)

# In-memory chat history keyed by session_id
sessions: dict[str, list] = {}


@app.route("/chat", methods=["POST"])
def chat():
    body         = request.get_json(force=True)
    session_id   = body.get("session_id", "default")
    user_message = body.get("message", "").strip()
    do_stream    = body.get("stream", True)   # streaming ON by default

    if not user_message:
        return jsonify({"error": "message is required"}), 400

    if session_id not in sessions:
        sessions[session_id] = []

    history = sessions[session_id]
    history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    # ── Non-streaming (original behaviour) ───────────────────────────────────
    if not do_stream:
        try:
            response = requests.post(
                f"{LM_STUDIO_BASE_URL}/chat/completions",
                json={"messages": messages, "temperature": 0.7, "stream": False},
                timeout=300,
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
            history.append({"role": "assistant", "content": reply})
            return jsonify({"reply": reply, "session_id": session_id})

        except requests.exceptions.ConnectionError:
            history.pop()
            return jsonify({"error": "Cannot connect to LM Studio at http://192.168.56.1:1234"}), 503
        except Exception as e:
            history.pop()
            return jsonify({"error": str(e)}), 500

    # ── Streaming ─────────────────────────────────────────────────────────────
    def generate():
        full_reply = []

        try:
            with requests.post(
                f"{LM_STUDIO_BASE_URL}/chat/completions",
                json={"messages": messages, "temperature": 0.7, "stream": True},
                stream=True,
                timeout=(10, 300),   # (connect timeout, read timeout)
            ) as r:
                r.raise_for_status()

                for raw_line in r.iter_lines():
                    if not raw_line:
                        continue

                    line = raw_line.decode("utf-8")

                    # SSE lines look like:  data: {...}
                    if not line.startswith("data:"):
                        continue

                    data_str = line[len("data:"):].strip()

                    # End-of-stream sentinel
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    delta = chunk["choices"][0].get("delta", {})
                    token = delta.get("content", "")

                    if token:
                        full_reply.append(token)
                        # Forward each token as an SSE event to the browser
                        yield f"data: {json.dumps({'token': token, 'session_id': session_id})}\n\n"

            # Save the completed reply to history once streaming is done
            history.append({"role": "assistant", "content": "".join(full_reply)})
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

        except requests.exceptions.ConnectionError:
            history.pop()
            yield f"data: {json.dumps({'error': 'Cannot connect to LM Studio at http://192.168.56.1:1234'})}\n\n"

        except Exception as e:
            if full_reply:
                # Partial reply — still save what we got
                history.append({"role": "assistant", "content": "".join(full_reply)})
            else:
                history.pop()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disables Nginx buffering if behind a proxy
        },
    )


@app.route("/reset", methods=["POST"])
def reset():
    body       = request.get_json(force=True)
    session_id = body.get("session_id", "default")
    sessions.pop(session_id, None)
    return jsonify({"status": "reset", "session_id": session_id})


@app.route("/health", methods=["GET"])
def health():
    try:
        resp   = requests.get(f"{LM_STUDIO_BASE_URL}/models", timeout=5)
        models = [m["id"] for m in resp.json().get("data", [])]
        return jsonify({"status": "ok", "lm_studio": "reachable", "models": models})
    except Exception as e:
        return jsonify({"status": "ok", "lm_studio": "unreachable", "error": str(e)}), 200


if __name__ == "__main__":
    # threaded=True is important — each streaming response holds a connection open
    app.run(port=5001, debug=True, threaded=True)