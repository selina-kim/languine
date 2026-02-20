import json
from flask import Blueprint, request, Response, send_file
from io import BytesIO
from services.deck_service import DeckService
from flask_jwt_extended import jwt_required, get_jwt_identity

decks_bp = Blueprint("decks", __name__)
deck_service = DeckService()


# Helper functions for creating JSON responses
def json_response(data, status=200, ensure_ascii=False):
    """Create a JSON response with proper encoding."""
    return Response(
        json.dumps(data, default=str, ensure_ascii=ensure_ascii),
        status=status,
        mimetype="application/json; charset=utf-8" if not ensure_ascii else "application/json"
    )

# Helper function for error responses
def error_response(message, status=500):
    """Create an error JSON response."""
    return json_response({"error": message}, status=status)


@decks_bp.route("/decks/<int:deck_id>/export", methods=["GET"])
@jwt_required()
def export_deck(deck_id: int):
    """
    Export a deck in specified format
    
    Query params:
    - format: Export format (json, csv, anki) - default: json
    
    Returns: File download with deck data
    """
    export_format = request.args.get("format", "json").lower()
    user_id = get_jwt_identity()
    
    # Fetch deck and cards from database
    try:
        deck_data = deck_service.get_deck_for_export(user_id, deck_id)
        
        if not deck_data:
            return error_response("Deck not found or access denied", status=404)
    
    except Exception as e:
        return error_response(f"Database error: {str(e)}")
    
    try:
        if export_format == "json":
            content = deck_service.export_deck_to_json(deck_data)
            mimetype = "application/json"
            filename = f"{deck_data['deck']['deck_name']}.json"
        
        elif export_format == "csv":
            content = deck_service.export_deck_to_csv(deck_data)
            mimetype = "text/csv"
            filename = f"{deck_data['deck']['deck_name']}.csv"
        
        elif export_format == "anki":
            content = deck_service.export_deck_to_anki(deck_data)
            mimetype = "text/plain"
            filename = f"{deck_data['deck']['deck_name']}.txt"
        
        else:
            return error_response(f"Unsupported export format: {export_format}", status=400)
        
        # Create file-like object for download
        buffer = BytesIO(content.encode('utf-8'))
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return error_response(f"Export failed: {str(e)}")


@decks_bp.route("/decks/import", methods=["POST"])
@jwt_required()
def import_deck():
    """
    Import a deck from file
    
    Form data:
    - file: The file to import (JSON, CSV, or TXT for Anki)
    - format: Import format (json, csv, anki) - optional, auto-detected from extension
    - deck_name: Name for the deck (required for CSV/Anki)
    - word_lang: Word language (required for CSV/Anki)
    - trans_lang: Translation language (required for CSV/Anki)
    
    Returns: JSON with imported deck data
    """
    if 'file' not in request.files:
        return error_response("No file provided", status=400)
    
    file = request.files['file']
    
    if file.filename == '':
        return error_response("No file selected", status=400)
    
    # Detect format from file extension or form data
    import_format = request.form.get('format')
    if not import_format:
        if file.filename.endswith('.json'):
            import_format = 'json'
        elif file.filename.endswith('.csv'):
            import_format = 'csv'
        elif file.filename.endswith('.txt'):
            import_format = 'anki'
        else:
            return error_response("Could not determine file format. Please specify 'format' parameter", status=400)
    
    try:
        file_content = file.read().decode('utf-8')
        
        if import_format == 'json':
            imported_data = deck_service.import_deck_from_json(file_content)
        
        elif import_format == 'csv':
            deck_name = request.form.get('deck_name')
            word_lang = request.form.get('word_lang')
            trans_lang = request.form.get('trans_lang')
            
            if not all([deck_name, word_lang, trans_lang]):
                return error_response("CSV import requires deck_name, word_lang, and trans_lang", status=400)
            
            imported_data = deck_service.import_deck_from_csv(
                file_content, deck_name, word_lang, trans_lang
            )
        
        elif import_format == 'anki':
            deck_name = request.form.get('deck_name')
            word_lang = request.form.get('word_lang')
            trans_lang = request.form.get('trans_lang')
            
            if not all([deck_name, word_lang, trans_lang]):
                return error_response("Anki import requires deck_name, word_lang, and trans_lang", status=400)
            
            imported_data = deck_service.import_deck_from_anki(
                file_content, deck_name, word_lang, trans_lang
            )
        
        else:
            return error_response(f"Unsupported import format: {import_format}", status=400)
        
        # Save imported deck and cards to database
        user_id = get_jwt_identity()
        result = deck_service.save_imported_deck(user_id, imported_data)
        
        return json_response({
            "message": "Deck imported successfully",
            **result
        }, status=201)
    
    except ValueError as e:
        return error_response(str(e), status=400)
    except Exception as e:
        return error_response(f"Import failed: {str(e)}")


@decks_bp.route("/decks/<int:deck_id>", methods=["GET"])
@jwt_required()
def get_deck(deck_id: int):
    """
    Get deck details and cards
    
    Returns: JSON with deck info and cards
    """
    user_id = get_jwt_identity()
    
    try:
        result = deck_service.get_deck_with_cards(user_id, deck_id)
        
        if not result:
            return error_response("Deck not found or access denied", status=404)
        
        return json_response(result)
    
    except Exception as e:
        return error_response(f"Database error: {str(e)}")


@decks_bp.route("/decks", methods=["GET"])
@jwt_required()
def list_decks():
    """
    List all decks for the authenticated user
    
    Returns: JSON array of decks
    """
    user_id = get_jwt_identity()
    
    try:
        decks = deck_service.list_user_decks(user_id)
        
        return json_response({
            "decks": decks
        })
    
    except Exception as e:
        return error_response(f"Database error: {str(e)}")


@decks_bp.route("/decks/new", methods=["POST"])
@jwt_required()
def create_deck():
    """
    Create a new deck
    
    Body:
    - deck_name: Name of the deck
    - word_lang: Language of words
    - trans_lang: Translation language
    - description: Optional description
    
    Returns: JSON with created deck info
    """
    try:
        data = request.get_json()
    except Exception:
        return error_response("No data provided", status=400)
    
    if not data:
        return error_response("No data provided", status=400)
    
    required_fields = ["deck_name", "word_lang", "trans_lang"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}", status=400)
    
    # Save deck to database
    user_id = get_jwt_identity()
    
    try:
        deck = deck_service.create_deck(user_id, data)
        
        return json_response({
            "message": "Deck created successfully",
            "deck": deck
        }, status=201)
    
    except Exception as e:
        return error_response(f"Database error: {str(e)}")
