from flask import Flask, jsonify
from flask_cors import CORS
from db import init_db, seed_db, seed_reviews, get_db
from routes.recipes import recipes_bp
from routes.ingredients import ingredients_bp
from routes.report import report_bp
from routes.reviews import reviews_bp

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Register blueprints
app.register_blueprint(recipes_bp)
app.register_blueprint(ingredients_bp)
app.register_blueprint(report_bp)
app.register_blueprint(reviews_bp)

@app.route('/greetings', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello World! CS34800 Recipe App'}), 200

if __name__ == '__main__':
    init_db()
    seed_db()
    conn = get_db()
    seed_reviews(conn)
    conn.close()
    app.run(debug=True)