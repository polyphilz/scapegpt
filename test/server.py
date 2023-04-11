from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def index():
    return jsonify({"res": "yay"})

if __name__ == "__main__":
    app.run(port=4747)
