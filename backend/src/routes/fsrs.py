from flask import Blueprint, Response, request
import json
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.fsrs_service import FsrsService, CardNotFoundError, InvalidGradeError, DatabaseError
from services.fsrs.optimizer import mini_batch_size


fsrs_bp = Blueprint("fsrs", __name__)
fsrs_service = FsrsService()

MIN_OPTIMIZATION_CARDS_THRESHOLD = mini_batch_size



# ── Helpers ───────────────────────────────────────────────────────────────────

def json_response(data, status=200):
    return Response(
        json.dumps(data, default=str, ensure_ascii=False),
        status=status,
        mimetype="application/json; charset=utf-8",
    )


def error_response(message, status=500):
    return json_response({"error": message}, status=status)


# ── Routes ────────────────────────────────────────────────────────────────────

@fsrs_bp.route("/reviews", methods=["POST"])
@jwt_required()
def log_review():
    """
    Log a single card review.

    Request body (JSON):
        card_id         (int, required)  – ID of the card that was reviewed.
        grade           (int, required)  – Recall quality: 1=Again 2=Hard 3=Good 4=Easy.
        review_duration (int, required)  – Time to recall in milliseconds.

    Returns 201 with the created review log on success.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", status=400)

    card_id = data.get("card_id")
    grade = data.get("grade")
    review_duration = data.get("review_duration")  

    # ── Validate required fields ───────────────────────────────────────────────
    if card_id is None:
        return error_response("card_id is required.", status=400)
    if grade is None:
        return error_response("grade is required.", status=400)
    if review_duration is None:
        return error_response("review_duration is required.", status=400)
    if not isinstance(card_id, int):
        return error_response("card_id must be an integer.", status=400)
    if not isinstance(grade, int):
        return error_response("grade must be an integer.", status=400)
    if not isinstance(review_duration, int):
        return error_response("review_duration must be an integer (milliseconds).", status=400)

    try:
        review_log = fsrs_service.log_review(card_id, grade, review_duration)
        fsrs_service.update_deck_last_review_date(card_id)
        fsrs_service.update_card_fail_success_count(card_id, grade)
        fsrs_service.review_card(card_id, grade)
        return json_response(review_log, status=201)
    

    except InvalidGradeError as e:
        return error_response(str(e), status=400)
    except CardNotFoundError as e:
        return error_response(str(e), status=404)
    except DatabaseError as e:
        return error_response(f"Database error: {str(e)}", status=500)
    

@fsrs_bp.route("/end-review", methods=["POST"])
@jwt_required()
def end_review():
    """
    Called by the frontend when a review session ends.

    Request body (JSON):
        total_cards_reviewed (int, required) – Number of UNIQUE cards reviewed in the session.

    If the user's total unique cards reviewed meets or exceeds the optimization
    threshold, their FSRS parameters will be re-optimized using their full
    review history and persisted to their account.

    Returns 200 with a message indicating whether optimization was triggered.
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON.", status=400)

    total_cards_reviewed = data.get("total_cards_reviewed")
    if total_cards_reviewed is None:
        return error_response("total_cards_reviewed is required.", status=400)
    if not isinstance(total_cards_reviewed, int):
        return error_response("total_cards_reviewed must be an integer.", status=400)

    user_id = get_jwt_identity()
    optimized = False

    try:
        # Update user's review counts for optimization tracking
        fsrs_service.increment_review_counts(user_id, total_cards_reviewed)

        # optimize the parameters if the user has automatic optimization enabled 
        # and has reviewed enough unique cards since the last optimization
        if fsrs_service.should_optimize(user_id):
            # check if they have reviewed enough unique cards since the last optimization
            # and that their total reviewed cards meets the min threshold for optimization mini_batch_size
            if fsrs_service.cards_reviewed_since_last_optimize(user_id) >= fsrs_service.num_reviews_per_optimize(user_id) and fsrs_service.total_cards_reviewed(user_id) >= MIN_OPTIMIZATION_CARDS_THRESHOLD:
                # optmize and save the parameters
                new_params = fsrs_service.optimize_parameters(user_id)
                fsrs_service.save_parameters(user_id, new_params)
                optimized = True
                # reset the reviewed_since_last_optimize count to 0 after optimization
                fsrs_service.reset_review_counts(user_id)  

                # reschedule all cards based on the new parameters
                fsrs_service.reschedule_all_cards(user_id)

        return json_response(
            {"message": "Review session ended.", "parameters_optimized": optimized},
            status=200,
        )
    except DatabaseError as e:
        return error_response(f"Database error: {str(e)}", status=500)

@fsrs_bp.route("/due-cards", methods=["GET"])
@jwt_required()
def get_due_cards():
    """
    Retrieve all cards currently due for review for the authenticated user.

    Returns 200 with a list of due cards and the total number of due cards.

    Cards are returned as a list of dictionaries with the following fields:
        - card_id 
        - due_date 
        - deck_id
    """
    user_id = get_jwt_identity()
    try:
        num_due_cards, due_cards = fsrs_service.get_due_cards(user_id)
        return json_response({"num_due_cards": num_due_cards, "due_cards": due_cards}, status=200)
    except DatabaseError as e:
        return error_response(f"Database error: {str(e)}", status=500)

@fsrs_bp.route("/num-due-cards", methods=["GET"])
@jwt_required()
def get_num_due_cards():
    """
    Retrieve the total number of cards currently due for review for the authenticated user.

    Returns 200 with the number of due cards.
    """
    user_id = get_jwt_identity()
    try:
        num_due_cards = fsrs_service.get_num_due_cards(user_id)
        return json_response({"num_due_cards": num_due_cards}, status=200)
    except DatabaseError as e:
        return error_response(f"Database error: {str(e)}", status=500)
