"""server.py
Flask API server for the secure messaging app.
"""
 
from flask import Flask, request, jsonify
from message_handler import MessageHandler
 
app = Flask(__name__)
handler = MessageHandler()
 
 
@app.route("/register", methods=["POST"])
def register():
    user_id = request.json.get("user_id", "").strip()
    if not user_id:
        return jsonify({"success": False, "error": "Missing user_id"}), 400
 
    success = handler.register_user(user_id)
    return jsonify({"success": success})
 
 
@app.route("/send", methods=["POST"])
def send():
    data = request.json
    sender = data.get("sender", "").strip()
    receiver = data.get("receiver", "").strip()
    message = data.get("message", "").strip()
 
    if not sender or not receiver or not message:
        return jsonify({"success": False, "error": "Missing fields"}), 400
 

    success = handler.send_message(sender, receiver, message)
    return jsonify({"success": success})
 
 
@app.route("/conversation", methods=["GET"])
def conversation():
    user_id = request.args.get("user_id", "").strip()
    contact = request.args.get("contact", "").strip()
 
    if not user_id or not contact:
        return jsonify([])
 
    convo = handler.get_conversation(user_id, contact)
    return jsonify(convo)
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
 
