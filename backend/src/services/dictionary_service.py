import requests
import os
import re

# call Merriam-Webster Dictionary API to extract english example sentences, pronunciation, audio url, and definitions for a word
# documentation: https://dictionaryapi.com/products/json
def call_dictionary_api(word):
    MW_DICT_API_KEY = os.getenv("MW_DICT_API_KEY")
    url = f"https://dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={MW_DICT_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}, 504
    except requests.exceptions.ConnectionError:
        return {"error": "Network connection error"}, 503
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}, 500

    if response.status_code == 429:
        return {"error": "Rate limit exceeded"}, 429
    
    if response.status_code != 200:
        return {"error": "Failed to fetch data"}, response.status_code

    # try to parse JSON response
    try:
        data = response.json()
    except requests.exceptions.JSONDecodeError:
        # API returned non-JSON
        return {"error": f"Invalid API response: {response.text}"}, 400

    # check if word was not found (API returns list of string suggestions)
    if data and isinstance(data[0], str):
        return {
            "word": word,
            "definitions": [{"definition": "Word not found", "example_sentences": []}],
            "pronunciation": None,
            "audio_url": None,
            "suggestions": data
        }

    # initialize variables
    pronunciation = None
    audio_url = None
    structured_defs = []

    # parse response data
    try:
        entry = data[0]

        # get pronunciation
        try:
            pronunciation = entry["hwi"]["prs"][0]["mw"]
        except (KeyError, IndexError, AttributeError):
            pass

        # get audio URL
        try:
            audio = entry["hwi"]["prs"][0]["sound"]["audio"]
            if audio.startswith("bix"):
                subdirectory = "bix"
            elif audio.startswith("gg"):
                subdirectory = "gg"
            elif audio[0].isdigit() or not audio[0].isalpha():
                subdirectory = "number"
            else:
                subdirectory = audio[0]
            audio_url = f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{subdirectory}/{audio}.mp3"
        except (KeyError, IndexError):
            pass

        # helper to clean MW markup
        def clean_text(text):
            if not text:
                return None
            text = re.sub(r"\{bc\}", "", text)
            text = re.sub(r"\{wi\}|\{\/wi\}", "", text)
            text = re.sub(r"\{sx\|.*?\|\|.*?\}", "", text)
            text = re.sub(r"\{a_link\|.*?\}", "", text)
            text = re.sub(r"\{.*?\}", "", text)
            text = text.replace("\u0027", "'")
            return text.strip()

        # extract definitions and example sentences
        if "def" in entry:
            for sense_block in entry["def"]:
                for sseq in sense_block["sseq"]:
                    for sense in sseq:
                        sense_data = sense[1]
                        if "dt" in sense_data:
                            last_obj = None
                            for dt_item in sense_data["dt"]:
                                if dt_item[0] == "text":
                                    cleaned_def = clean_text(dt_item[1])
                                    if cleaned_def:
                                        obj = {"definition": cleaned_def, "example_sentences": []}
                                        structured_defs.append(obj)
                                        last_obj = obj
                                elif dt_item[0] == "vis":
                                    vis_list = dt_item[1]
                                    examples = []
                                    for v in vis_list:
                                        if "t" in v:
                                            cleaned_vis = clean_text(v["t"])
                                            if cleaned_vis:
                                                examples.append(cleaned_vis)
                                    if last_obj:
                                        last_obj["example_sentences"].extend(examples)

        # fallback to shortdef if nothing found
        if not structured_defs and "shortdef" in entry:
            structured_defs = [{"definition": clean_text(d), "example_sentences": []} for d in entry["shortdef"]]

        # fallback for nothing found
        if not structured_defs:
            structured_defs = [{"definition": "Definition not found", "example_sentences": []}]

    except (KeyError, IndexError, TypeError):
        return {
            "word": word,
            "definitions": [{"definition": "Definition not found", "example_sentences": []}],
            "pronunciation": pronunciation,
            "audio_url": audio_url
        }

    return {
        "word": word,
        "definitions": structured_defs,
        "pronunciation": pronunciation,
        "audio_url": audio_url
    }