from flask import Blueprint, jsonify, request
from db import get_db, begin_transaction

reviews_bp = Blueprint('reviews', __name__)


@reviews_bp.route('/recipes/<int:recipe_id>/reviews', methods=['GET'])
def get_reviews(recipe_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM Recipes WHERE id = ?', (recipe_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Recipe not found'}), 404

    cursor.execute('''
        SELECT r.id, r.rating, r.comment, r.created_at,
               u.id AS user_id, u.name AS user_name
        FROM Reviews r
        JOIN Users u ON r.user_id = u.id
        WHERE r.recipe_id = ?
        ORDER BY r.created_at DESC
    ''', (recipe_id,))
    reviews = [dict(row) for row in cursor.fetchall()]

    # Aggregate stats
    cursor.execute('''
        SELECT
            COUNT(*) AS review_count,
            ROUND(AVG(rating), 2) AS avg_rating,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) AS five_star,
            SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) AS four_star,
            SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) AS three_star,
            SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) AS two_star,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) AS one_star
        FROM Reviews
        WHERE recipe_id = ?
    ''', (recipe_id,))
    stats = dict(cursor.fetchone())

    conn.close()
    return jsonify({'stats': stats, 'reviews': reviews}), 200


@reviews_bp.route('/recipes/<int:recipe_id>/reviews', methods=['POST'])
def create_review(recipe_id):
    """
    Transaction Isolation: SERIALIZABLE
    Justification: This endpoint performs a check-then-insert pattern:
    it first verifies the recipe and user exist (two SELECTs), then
    inserts the review.  SERIALIZABLE is the strongest isolation level
    — it prevents dirty reads, non-repeatable reads, AND phantom reads.
    This is necessary here because without full serialisation, another
    transaction could DELETE the recipe or user between our existence
    checks and the INSERT, causing a referential integrity violation.
    SERIALIZABLE ensures that the entire check-then-insert sequence
    executes as if no other transaction is running concurrently.
    """
    data = request.get_json()

    if 'user_id' not in data or 'rating' not in data:
        return jsonify({'error': 'user_id and rating are required'}), 400
    if not (1 <= int(data['rating']) <= 5):
        return jsonify({'error': 'rating must be between 1 and 5'}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        begin_transaction(conn, 'SERIALIZABLE')

        cursor.execute('SELECT id FROM Recipes WHERE id = ?', (recipe_id,))
        if not cursor.fetchone():
            conn.rollback()
            conn.close()
            return jsonify({'error': 'Recipe not found'}), 404

        cursor.execute('SELECT id FROM Users WHERE id = ?', (data['user_id'],))
        if not cursor.fetchone():
            conn.rollback()
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        cursor.execute('''
            INSERT INTO Reviews (recipe_id, user_id, rating, comment)
            VALUES (?, ?, ?, ?)
        ''', (recipe_id, data['user_id'], data['rating'], data.get('comment')))
        conn.commit()
        review_id = cursor.lastrowid
    except Exception as e:
        conn.rollback()
        conn.close()
        # UNIQUE constraint means this user already reviewed this recipe
        return jsonify({'error': 'User has already reviewed this recipe'}), 409

    conn.close()
    return jsonify({'message': 'Review created', 'id': review_id}), 201


@reviews_bp.route('/reviews/<int:review_id>', methods=['PUT'])
def update_review(review_id):
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM Reviews WHERE id = ?', (review_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Review not found'}), 404

    if 'rating' in data and not (1 <= int(data['rating']) <= 5):
        conn.close()
        return jsonify({'error': 'rating must be between 1 and 5'}), 400

    cursor.execute('''
        UPDATE Reviews
        SET rating = ?, comment = ?
        WHERE id = ?
    ''', (data['rating'], data.get('comment'), review_id))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Review updated'}), 200


@reviews_bp.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM Reviews WHERE id = ?', (review_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Review not found'}), 404

    cursor.execute('DELETE FROM Reviews WHERE id = ?', (review_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Review deleted'}), 200


@reviews_bp.route('/users', methods=['GET'])
def get_users():
    """Return all users — for populating reviewer dropdowns dynamically."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email FROM Users ORDER BY name')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(users), 200