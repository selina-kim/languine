from flask import Blueprint, Response
import json
from src.services.dictionary_api import *

define_bp = Blueprint("define", __name__)

# test using http://localhost:8080/define/soup
@define_bp.route("/define/<word>")
# get english define sentences, pronunciation, audio url, and definitions for a word
def define_sentence(word):
    # get result from merriam webster dictionary api 
    result = call_dictionary_api(word)
    # error case (payload, status_code)
    if isinstance(result, tuple):  
        payload, status = result
        return Response(
            json.dumps(payload, ensure_ascii=False, indent=None),
            status=status,
            mimetype="application/json"
        )
    
    # normal case
    return Response(
        json.dumps(result, ensure_ascii=False, indent=None),
        mimetype="application/json"
    )

