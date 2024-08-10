from app import app, db
from app.models import User, Reaction, News, ReactionLikeIt, ReactionHateIt
from app.utils import *
from flask import jsonify, request
from flask_cors import cross_origin
from datetime import datetime as dt
from flask_jwt_extended import get_jwt_identity, jwt_required
from config import Config
from sqlalchemy.orm import joinedload

@app.route('/api/reactions', methods=['GET'])
@cross_origin()
def get_reactions():
    try:
        all_reactions = Reaction.query.all()
        results = []
        for reaction in all_reactions:
            temp = {}
            temp['content'] = reaction.content
            temp['author'] = reaction.user.name if reaction.user else None
            temp['guest_author'] = reaction.guest_author if reaction.guest_author else None
            temp['author_picture'] = reaction.user.picture if reaction.user else None
            results.append(temp)
        return results
    except Exception as e:
        return {"msg": str(e)}, 401


@app.route('/api/reactions', methods=['POST'])
@cross_origin()
@jwt_required(optional=True)
def create_reaction():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"message": "No input data provided"}), 400
        
        current_user = get_jwt_identity()
        user = User.query.filter_by(login=current_user).first_or_404() if current_user else None
        
        new_reaction = Reaction(news_id=data["news_id"], content=data["content"], guest_author=data["guest_author"] if not user else None, user_id=user.id if user else None)
        
        db.session.add(new_reaction)
        db.session.commit()
        return jsonify({"message": "Reaction created successfully", "location": f'/reactions/{new_reaction.id}'}), 201
    except Exception as e:
        return {"msg": str(e)}, 401
    
    
@app.route('/api/reactions/<int:reaction_id>', methods=['PUT'])
@cross_origin()
@jwt_required()
def update_reaction(reaction_id):
    try:
        data = request.get_json()
        
        if not data or not data["content"]:
            return jsonify({"message": "No input data provided or missing data"}), 400
        
        current_user = get_jwt_identity()
        user = User.query.filter_by(login=current_user).first_or_404()
        reaction = Reaction.query.filter(
            (Reaction.id == reaction_id) & 
            ((Reaction.user_id == user.id) | (user.id == Config.admin_id))
        ).first_or_404()
        
        reaction.content = data["content"]
        reaction.last_update = dt.utcnow()
        
        db.session.commit()
        
        return jsonify({"message": "Reaction updated successfully", "location": f'/reactions/{reaction.id}'}), 200
    except Exception as e:
        return {"msg": str(e)}, 401
    

@app.route('/api/reactions/<int:reaction_id>', methods=['DELETE'])
@cross_origin()
@jwt_required()
def delete_reaction(reaction_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.filter_by(login=current_user).first_or_404()

        reaction_to_delete = Reaction.query.filter(
            (Reaction.id == reaction_id)
        ).join(News).filter(
            (Reaction.user_id == user.id) | 
            (user.id == Config.admin_id) | 
            (News.user_id == user.id)
        ).first_or_404()

        db.session.delete(reaction_to_delete)
        db.session.commit()

        return jsonify({"msg": "Reaction deleted successfully"}), 200
    except Exception as e:
        return jsonify({"msg": str(e)}), 401
    

@app.route('/api/reactions/like/<int:reaction_id>', methods=['POST'])
@cross_origin()
@jwt_required()
def add_like_reaction(reaction_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.filter_by(login=current_user).first_or_404()
        reaction = Reaction.query.filter((Reaction.id == reaction_id)).first_or_404()
        
        like_exists = ReactionLikeIt.query.filter_by(user_id=user.id, reaction_id=reaction.id).first()
        hate_exists = ReactionHateIt.query.filter_by(user_id=user.id, reaction_id=reaction.id).first()
        if like_exists or hate_exists:
            return jsonify({"message": "Like od Hate already exists"}), 200
        else:    
            new_like = ReactionLikeIt(user_id=user.id, reaction_id=reaction.id)
            db.session.add(new_like)
            db.session.commit()
            return jsonify({"message": "Like added succesfully"}), 200
        
    except Exception as e:
        return jsonify({"msg": str(e)}), 401
    
    
@app.route('/api/reaction/like/<int:reaction_id>', methods=['DELETE'])
@cross_origin()
@jwt_required()
def delete_like_reaction(reaction_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.filter_by(login=current_user).first_or_404()
        reaction = Reaction.query.filter((Reaction.id == reaction_id)).first_or_404()
    
        like_to_delete = ReactionLikeIt.query.filter_by(user_id=user.id, reaction_id=reaction.id).first()
        if like_to_delete:
            db.session.delete(like_to_delete)
            db.session.commit()
            return jsonify({"message": "Like deleted succesfully"}), 200
        else:
            return jsonify({"message": "Like not exists"}), 200
        
    except Exception as e:
        return jsonify({"msg": str(e)}), 401
    
    
@app.route('/api/reactions/<string:action>/<int:reaction_id>', methods=['POST', 'DELETE'])
@cross_origin()
@jwt_required()
def manage_reaction_reactions(action, reaction_id):
    try:
        current_user = get_jwt_identity()
        user = User.query.filter_by(login=current_user).first_or_404()
        reaction = Reaction.query.filter_by(id=reaction_id).first_or_404()

        like_exists = ReactionLikeIt.query.filter_by(user_id=user.id, reaction_id=reaction.id).first()
        hate_exists = ReactionHateIt.query.filter_by(user_id=user.id, reaction_id=reaction.id).first()

        if action == 'like':
            opposite_reaction = hate_exists
            existing_reaction = like_exists
            reaction_class = ReactionLikeIt
            opposite_msg = "Hate removed. "
            reaction_msg = "Like added successfully"
            delete_msg = "Like deleted successfully"
            not_exists_msg = "Like does not exist"
        elif action == 'hate':
            opposite_reaction = like_exists
            existing_reaction = hate_exists
            reaction_class = ReactionHateIt
            opposite_msg = "Like removed. "
            reaction_msg = "Hate added successfully"
            delete_msg = "Hate deleted successfully"
            not_exists_msg = "Hate does not exist"
        else:
            return jsonify({"message": "Invalid action"}), 400

        if request.method == 'POST':
            if existing_reaction:
                return jsonify({"message": f"{action.capitalize()} already exists"}), 200

            if opposite_reaction:
                db.session.delete(opposite_reaction)
                db.session.commit()

            new_reaction = reaction_class(user_id=user.id, reaction_id=reaction.id)
            db.session.add(new_reaction)
            db.session.commit()
            return jsonify({"message": opposite_msg + reaction_msg}), 200

        elif request.method == 'DELETE':
            if existing_reaction:
                db.session.delete(existing_reaction)
                db.session.commit()
                return jsonify({"message": delete_msg}), 200

            return jsonify({"message": not_exists_msg}), 200

    except Exception as e:
        return jsonify({"message": str(e)}), 401