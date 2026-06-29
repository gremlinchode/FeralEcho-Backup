import logging
from flask import Flask, request, jsonify

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

app = Flask(__name__)

# Simulated Echo state
echo_state = {"messages": []}

@app.route("/message", methods=["POST"])
def handle_message():
    data = request.json
    logging.debug(f"Received data: {data}")
    
    user_message = data.get("message", "")
    # For now, Echo just echoes back the message
    response_text = f"Echo received: {user_message}"
    
    echo_state["messages"].append({"user": user_message, "echo": response_text})
    logging.debug(f"Updated state: {echo_state}")
    
    return jsonify({"response": response_text, "state": echo_state})

@app.route("/state", methods=["GET"])
def get_state():
    logging.debug("State requested")
    return jsonify(echo_state)

if __name__ == "__main__":
    logging.info("=== Starting Flask Echo Test Server ===")
    app.run(host="127.0.0.1", port=5000, debug=True)

