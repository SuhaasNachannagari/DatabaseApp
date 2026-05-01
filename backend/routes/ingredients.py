from flask import Blueprint, jsonify, request
from db import get_db

ingredients_bp = Blueprint('ingredients', __name__)


@ingredients_bp.route('/ingredients', methods=['GET'])
def get_ingredients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Ingredients ORDER BY category, name')
    ingredients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(ingredients), 200


@ingredients_bp.route('/ingredients', methods=['POST'])
def create_ingredient():
    data = request.get_json()
    required = ['name', 'unit', 'category']
    if not all(k in data for k in required):
        return jsonify({'error': f'Missing required fields: {required}'}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO Ingredients (name, unit, category) VALUES (?, ?, ?)',
            (data['name'], data['unit'], data['category'])
        )
        conn.commit()
        ingredient_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

    conn.close()
    return jsonify({'message': 'Ingredient created', 'id': ingredient_id}), 201


@ingredients_bp.route('/ingredients/<int:ingredient_id>', methods=['DELETE'])
def delete_ingredient(ingredient_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM Ingredients WHERE id = ?', (ingredient_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Ingredient not found'}), 404

    cursor.execute('DELETE FROM Ingredients WHERE id = ?', (ingredient_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Ingredient deleted'}), 200