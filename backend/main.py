from flask import Flask, jsonify 
from flask_cors import CORS

app = Flask(__name__)

app.config.from_object(__name__)

CORS(app, resources = {r"/*": {"origins": "*"}})
CORS(app, resources = {r"/*": {"origins": "http://localhost:8080", "allow_headers": "Access-Control-Allow-Origin"}})

# Hello world tour 
@app.route('/greetings', methods=['GET'])
def hello():
  return "Hello World! CS34800 project"


if __name__ == '__main__':
  # Run the app development mode
  app.run(debug=True)
    