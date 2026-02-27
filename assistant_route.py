"""
assistant_route.py  –  Blueprint that handles /assistant and /assistant/reset
Registered in app.py via:  app.register_blueprint(assistant_bp)
"""

import requests
from flask import Blueprint, request, jsonify, Response, stream_with_context

assistant_bp = Blueprint('assistant', __name__)

# ── Point this at your lmstudio_server.py ────────────────────────────────────
LM_STUDIO_SERVER = 'http://127.0.0.1:5001'   # NO trailing slash, NO leading space


@assistant_bp.route('/assistant', methods=['GET', 'POST'])
def assistant():
    if request.method == 'GET':
        return open('chatbot.html').read(), 200, {'Content-Type': 'text/html'}

    # ── Read body ONCE before entering any generator ──────────────────────────
    body       = request.get_json(force=True, silent=True) or {}
    message    = body.get('message', '').strip()
    session_id = body.get('session_id', 'default')
    do_stream  = body.get('stream', True)

    if not message:
        return jsonify({'error': 'message is required'}), 400

    # ── Streaming path ────────────────────────────────────────────────────────
    if do_stream:
        # All variables captured here in the outer scope — NOT inside generate()
        payload = {
            'message':    message,
            'session_id': session_id,
            'stream':     True,
        }

        def generate():
            try:
                with requests.post(
                    f'{LM_STUDIO_SERVER}/chat',
                    json=payload,
                    stream=True,
                    timeout=(10, 300),
                ) as r:
                    r.raise_for_status()
                    for chunk in r.iter_content(chunk_size=None):
                        if chunk:
                            yield chunk
            except requests.exceptions.ConnectionError:
                yield b'data: {"error": "Cannot reach LM Studio backend at ' + LM_STUDIO_SERVER.encode() + b'"}\n\n'
            except Exception as e:
                yield f'data: {{"error": "{str(e)}"}}\n\n'.encode()

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control':    'no-cache',
                'X-Accel-Buffering': 'no',
            },
        )

    # ── Non-streaming fallback ────────────────────────────────────────────────
    try:
        resp = requests.post(
            f'{LM_STUDIO_SERVER}/chat',
            json={'message': message, 'session_id': session_id, 'stream': False},
            timeout=300,
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Cannot reach LM Studio backend at {LM_STUDIO_SERVER}'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@assistant_bp.route('/assistant/reset', methods=['POST'])
def assistant_reset():
    body = request.get_json(force=True, silent=True) or {}
    try:
        resp = requests.post(
            f'{LM_STUDIO_SERVER}/reset',
            json=body,
            timeout=10,
        )
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500