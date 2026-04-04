import json
from flask import Blueprint, request, Response, send_file
from io import BytesIO
from services.deck_service import DeckService, DuplicateDeckNameError, UserNotFoundError, DatabaseError
from services.deck_import_export_service import DeckImportExportService
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
    
    except Exception:
        return error_response("Database error")
    
    try:
        if export_format == "json":
            content = DeckImportExportService.export_deck_to_json(deck_data)
            mimetype = "application/json"
            filename = f"{deck_data['deck']['deck_name']}.json"
        
        elif export_format == "csv":
            content = DeckImportExportService.export_deck_to_csv(deck_data)
            mimetype = "text/csv"
            filename = f"{deck_data['deck']['deck_name']}.csv"
        
        elif export_format == "anki":
            content = DeckImportExportService.export_deck_to_anki(deck_data)
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
    
    except Exception:
        return error_response("Database error")


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
            imported_data = DeckImportExportService.import_deck_from_json(file_content)
        
        elif import_format == 'csv':
            deck_name = request.form.get('deck_name')
            word_lang = request.form.get('word_lang')
            trans_lang = request.form.get('trans_lang')
            
            if not all([deck_name, word_lang, trans_lang]):
                return error_response("CSV import requires deck_name, word_lang, and trans_lang", status=400)
            
            imported_data = DeckImportExportService.import_deck_from_csv(
                file_content, deck_name, word_lang, trans_lang
            )
        
        elif import_format == 'anki':
            deck_name = request.form.get('deck_name')
            word_lang = request.form.get('word_lang')
            trans_lang = request.form.get('trans_lang')
            
            if not all([deck_name, word_lang, trans_lang]):
                return error_response("Anki import requires deck_name, word_lang, and trans_lang", status=400)
            
            imported_data = DeckImportExportService.import_deck_from_anki(
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
    except Exception:
        return error_response("Import failed")


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
    
    except Exception:
        return error_response("Database error")


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
    
    except Exception:
        return error_response("Database error")


@decks_bp.route("/decks/new", methods=["POST"])
@jwt_required()
def create_deck():
    """
    Create a new deck

    Body:
    - deck_name: Name of the deck (required, non-empty)
    - word_lang: Language of words (required)
    - trans_lang: Translation language (required)
    - description: Optional description
    - is_public: Optional boolean (default False)
    - link: Optional string

    Returns: JSON with created deck info
    """
    # Parse JSON safely (no exception on malformed JSON)
    data = request.get_json(silent=True)
    if not data:
        return error_response("No data provided", status=400)

    # Validate required fields exist
    required_fields = ["deck_name", "word_lang", "trans_lang"]
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}", status=400)

    # Validate deck_name is not blank
    if not str(data.get("deck_name", "")).strip():
        return error_response("deck_name is required and cannot be empty", status=400)

    # (Optional) Normalize some inputs
    data["deck_name"] = str(data["deck_name"]).strip()
    data["word_lang"] = str(data["word_lang"]).strip()
    data["trans_lang"] = str(data["trans_lang"]).strip()

    # Save deck to database
    user_id = get_jwt_identity()

    try:
        deck = deck_service.create_deck(user_id, data)

        return json_response(
            {
                "message": "Deck created successfully",
                "deck": deck,
            },
            status=201,
        )

    except DuplicateDeckNameError as e:
        return error_response(str(e) or "A deck with this name already exists for you", status=409)

    except UserNotFoundError as e:
        return error_response(str(e) or "User not registered", status=401)

    except DatabaseError:
        return error_response("Database error", status=500)

    except Exception:
        return error_response("Database error", status=500)


@decks_bp.route("/decks/due", methods=["GET"])
@jwt_required()
def get_decks_with_due_cards():
    """
    Get decks that have cards due for review
    
    Query params:
    - limit: Number of decks to return (default: 3)
    
    Returns: JSON with list of decks containing due_count and total_cards
    """
    user_id = get_jwt_identity()
    limit = request.args.get("limit", 3, type=int)
    limit = min(max(limit, 1), 20)  # Clamp between 1 and 20
    
    try:
        decks = deck_service.get_decks_with_due_cards(user_id, limit)
        return json_response({"decks": decks})
    
    except Exception:
        return error_response("Database error")


@decks_bp.route("/decks/recent", methods=["GET"])
@jwt_required()
def get_recent_decks():
    """
    Get most recently reviewed decks
    
    Query params:
    - limit: Number of decks to return (default: 3)
    
    Returns: JSON with list of recently reviewed decks
    """
    user_id = get_jwt_identity()
    limit = request.args.get("limit", 3, type=int)
    limit = min(max(limit, 1), 10)  # Clamp between 1 and 10
    
    try:
        decks = deck_service.get_recent_decks(user_id, limit)
        return json_response({"decks": decks})
    
    except Exception:
        return error_response("Database error")


@decks_bp.route("/decks/<int:deck_id>", methods=["PUT"])
@jwt_required()
def update_deck(deck_id: int):
    """
    Update an existing deck
    
    Body: (all fields optional)
    - deck_name: Name of the deck
    - word_lang: Language of learning words
    - trans_lang: Language the user knows
    - description: Description
    - is_public: Boolean
    - link: Link string
    
    Returns: JSON with updated deck info
    """
    data = request.get_json(silent=True)
    if not data:
        return error_response("No data provided", status=400)
    
    # Validate deck_name if provided
    if "deck_name" in data:
        deck_name = str(data["deck_name"]).strip()
        if not deck_name:
            return error_response("deck_name cannot be empty", status=400)
        data["deck_name"] = deck_name
    
    # Normalize other string fields if present
    if "word_lang" in data:
        data["word_lang"] = str(data["word_lang"]).strip()
    if "trans_lang" in data:
        data["trans_lang"] = str(data["trans_lang"]).strip()
    
    user_id = get_jwt_identity()
    
    try:
        updated_deck = deck_service.update_deck(user_id, deck_id, data)
        
        if not updated_deck:
            return error_response("Deck not found or access denied", status=404)
        
        return json_response({
            "message": "Deck updated successfully",
            "deck": updated_deck
        })
    
    except DuplicateDeckNameError as e:
        return error_response(str(e) or "A deck with this name already exists for you", status=409)
    
    except DatabaseError:
        return error_response("Database error", status=500)
    
    except Exception:
        return error_response("Database error", status=500)


@decks_bp.route("/decks/<int:deck_id>", methods=["DELETE"])
@jwt_required()
def delete_deck(deck_id: int):
    """
    Delete a deck and all its cards
    
    Returns: JSON with success message
    """
    user_id = get_jwt_identity()
    
    try:
        deleted = deck_service.delete_deck(user_id, deck_id)
        
        if not deleted:
            return error_response("Deck not found or access denied", status=404)
        
        return json_response({
            "message": "Deck deleted successfully"
        })
    
    except DatabaseError:
        return error_response("Database error", status=500)
    
    except Exception:
        return error_response("Database error", status=500)
