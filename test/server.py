from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/", methods=["POST"])
def index():
    # Print out the request method, headers, and body
    print(f"Request method: {request.method}")
    print(f"Request headers: {request.headers}")
    print(f"Request body: {request.get_data()}")

    return jsonify({"res": "yay"})

if __name__ == "__main__":
    app.run(port=4747)
