"""server.py
Flask API server for the secure messaging app.
"""
from flask import Flask, request, jsonify
from message_handler import MessageHandler
 
app = Flask(__name__)
handler = MessageHandler()
 
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    success = handler.register_user(data.get("user_id", ""), data.get("public_key", ""))
    return jsonify({"success": success})

@app.route("/get_key", methods=["GET"])
def get_key():
    public_key = handler.get_public_key(request.args.get("user_id", ""))
    if public_key:
        return jsonify({"success": True, "public_key": public_key})
    return jsonify({"success": False})

@app.route("/init_session", methods=["POST"])
def init_session():
    data = request.json
    success = handler.store_session(
        data.get("sender"), data.get("receiver"), 
        data.get("sender_key"), data.get("receiver_key")
    )
    return jsonify({"success": success})

@app.route("/get_session", methods=["GET"])
def get_session():
    session_data = handler.get_session(request.args.get("user_id"), request.args.get("contact"))
    if session_data:
        return jsonify({"success": True, "wrapped_key": session_data["my_key"]})
    return jsonify({"success": False})
 
@app.route("/send", methods=["POST"])
def send():
    data = request.json
    success = handler.send_message(data.get("sender"), data.get("receiver"), data.get("ciphertext"))
    return jsonify({"success": success})
 
@app.route("/conversation", methods=["GET"])
def conversation():
    convo = handler.get_conversation(request.args.get("user_id"), request.args.get("contact"))
    return jsonify(convo)
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)