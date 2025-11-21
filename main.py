import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from database import db, create_document, get_documents
from schemas import Preference, Suggestion, Generation

app = FastAPI(title="Baby Name Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Baby Name Generator API is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# ---------------------------------------------
# Baby name knowledge base (seed list)
# ---------------------------------------------

BASIC_NAMES: List[Dict[str, Any]] = [
    # English/Christian/Classic
    {"name": "James", "gender": "boy", "origin": "English", "meaning": "supplanter", "themes": ["classic", "biblical"], "popularity": 0.2},
    {"name": "Elizabeth", "gender": "girl", "origin": "English", "meaning": "oath of God", "themes": ["classic", "biblical"], "popularity": 0.2},
    {"name": "Grace", "gender": "girl", "origin": "English", "meaning": "grace", "themes": ["virtue", "classic"], "popularity": 0.15},

    # Irish/Celtic
    {"name": "Aoife", "gender": "girl", "origin": "Irish", "meaning": "beauty, radiance", "themes": ["celtic", "myth"], "popularity": 0.02},
    {"name": "Finn", "gender": "boy", "origin": "Irish", "meaning": "fair", "themes": ["celtic", "modern"], "popularity": 0.08},

    # Indian/Hindu
    {"name": "Aarav", "gender": "boy", "origin": "Sanskrit", "meaning": "peaceful", "themes": ["hindu", "virtue"], "popularity": 0.1},
    {"name": "Anaya", "gender": "girl", "origin": "Sanskrit", "meaning": "caring, protection", "themes": ["hindu", "virtue"], "popularity": 0.09},

    # Arabic/Muslim
    {"name": "Zayd", "gender": "boy", "origin": "Arabic", "meaning": "growth, abundance", "themes": ["muslim", "virtue"], "popularity": 0.04},
    {"name": "Layla", "gender": "girl", "origin": "Arabic", "meaning": "night", "themes": ["muslim", "poetic"], "popularity": 0.14},

    # Spanish/Latino
    {"name": "Mateo", "gender": "boy", "origin": "Spanish", "meaning": "gift of God", "themes": ["biblical", "classic"], "popularity": 0.18},
    {"name": "Sofia", "gender": "girl", "origin": "Greek/Spanish", "meaning": "wisdom", "themes": ["classic"], "popularity": 0.2},

    # African (Yoruba, Swahili)
    {"name": "Asha", "gender": "girl", "origin": "Swahili", "meaning": "life, hope", "themes": ["virtue", "nature"], "popularity": 0.05},
    {"name": "Kehinde", "gender": "boy", "origin": "Yoruba", "meaning": "second-born of twins", "themes": ["heritage"], "popularity": 0.01},

    # Chinese
    {"name": "Wei", "gender": "unisex", "origin": "Chinese", "meaning": "great, mighty", "themes": ["virtue"], "popularity": 0.06},
    {"name": "Mei", "gender": "girl", "origin": "Chinese", "meaning": "beautiful", "themes": ["virtue"], "popularity": 0.07},

    # Hebrew/Jewish
    {"name": "Noah", "gender": "boy", "origin": "Hebrew", "meaning": "rest, comfort", "themes": ["biblical", "classic"], "popularity": 0.22},
    {"name": "Miriam", "gender": "girl", "origin": "Hebrew", "meaning": "wished-for child", "themes": ["biblical", "classic"], "popularity": 0.03},

    # Greek/Myth
    {"name": "Atlas", "gender": "boy", "origin": "Greek", "meaning": "bearer of the heavens", "themes": ["myth", "modern"], "popularity": 0.05},
    {"name": "Iris", "gender": "girl", "origin": "Greek", "meaning": "rainbow", "themes": ["nature", "myth"], "popularity": 0.09},

    # Slavic
    {"name": "Mila", "gender": "girl", "origin": "Slavic", "meaning": "gracious, dear", "themes": ["modern", "virtue"], "popularity": 0.16},
    {"name": "Nikolai", "gender": "boy", "origin": "Slavic", "meaning": "victory of the people", "themes": ["classic"], "popularity": 0.04},

    # Japanese
    {"name": "Ren", "gender": "unisex", "origin": "Japanese", "meaning": "lotus, love", "themes": ["nature", "modern"], "popularity": 0.05},
    {"name": "Sora", "gender": "unisex", "origin": "Japanese", "meaning": "sky", "themes": ["nature"], "popularity": 0.03},
]

# ---------------------------------------------
# Scoring and generation logic
# ---------------------------------------------

def score_name(pref: Preference, item: Dict[str, Any]) -> float:
    score = 0.0

    # Gender match
    if pref.gender:
        if item.get("gender") == pref.gender or (pref.gender == "unisex" and item.get("gender") == "unisex"):
            score += 2
        else:
            score -= 0.5

    # Culture/origin
    if pref.cultures:
        if item.get("origin") and any(c.lower() in item["origin"].lower() for c in pref.cultures):
            score += 1.5

    # Languages/themes as soft preference
    if pref.languages:
        if any(lang.lower() in ",".join(item.get("themes", [])).lower() for lang in pref.languages):
            score += 0.5

    # Beliefs/themes
    if pref.beliefs:
        if any(b.lower() in ",".join(item.get("themes", [])).lower() for b in pref.beliefs):
            score += 1

    # Style/themes
    if pref.style:
        if pref.style.lower() in ",".join(item.get("themes", [])).lower():
            score += 1

    # Starts with / length
    if pref.starts_with and item["name"].lower().startswith(pref.starts_with.lower()):
        score += 0.8
    if pref.max_length and len(item["name"]) <= pref.max_length:
        score += 0.4

    # Surname flow heuristic (avoid alliteration unless style is classic; avoid rhyme with siblings)
    if pref.surname:
        n = item["name"].lower()
        s = pref.surname.lower()
        if n[0] == s[0]:
            score -= 0.2
        if len(n) > 2 and len(s) > 2 and n[-2:] == s[-2:]:
            score -= 0.2

    # Uniqueness vs popularity
    pop = float(item.get("popularity", 0.1))  # 0 to 1
    if pref.uniqueness == "unique":
        score += max(0, 0.8 - pop)
    elif pref.uniqueness == "common":
        score += pop
    else:
        score += 0.5 * (0.6 - abs(pop - 0.6))  # balanced toward mid-popular

    # Sibling similarity penalty
    for sib in pref.sibling_names:
        if sib:
            sib_l = sib.lower()
            # penalize same starting letter and rhyming endings
            if item["name"].lower().startswith(sib_l[:1]):
                score -= 0.3
            if len(sib_l) > 2 and item["name"].lower().endswith(sib_l[-2:]):
                score -= 0.3

    return score


def generate_suggestions(pref: Preference, limit: int = 12) -> List[Suggestion]:
    ranked = []
    for item in BASIC_NAMES:
        s = score_name(pref, item)
        if pref.max_length and len(item["name"]) > pref.max_length:
            continue
        if pref.gender and item.get("gender") not in [pref.gender, "unisex"]:
            continue
        ranked.append((s, item))

    ranked.sort(key=lambda x: x[0], reverse=True)
    top = []
    for score, item in ranked[:limit]:
        top.append(Suggestion(
            name=item["name"],
            gender=item.get("gender"),
            origin=item.get("origin"),
            meaning=item.get("meaning"),
            themes=item.get("themes", []),
            score=round(score, 3),
            rationale="Ranked using your preferences for culture, themes, style, and flow with your surname"
        ))
    return top


class GenerateRequest(Preference):
    quantity: Optional[int] = 12

class GenerateResponse(BaseModel):
    suggestions: List[Suggestion]


@app.post("/api/generate", response_model=GenerateResponse)
def api_generate(req: GenerateRequest):
    pref = Preference(**req.model_dump())
    qty = req.quantity or 12
    suggestions = generate_suggestions(pref, limit=qty)

    # Persist generation event
    try:
        gen = Generation(preference=pref, suggestions=suggestions)
        create_document("generation", gen)
    except Exception:
        # If DB is unavailable, proceed without failing the request
        pass

    return GenerateResponse(suggestions=suggestions)


@app.get("/api/history")
def api_history(limit: int = 10):
    try:
        docs = get_documents("generation", {}, limit)
        # Convert ObjectId and datetimes to strings for JSON
        def coerce(d):
            d = dict(d)
            if "_id" in d:
                d["_id"] = str(d["_id"])
            if "created_at" in d:
                d["created_at"] = str(d["created_at"]) 
            if "updated_at" in d:
                d["updated_at"] = str(d["updated_at"]) 
            # Strip heavy preference data if any
            return d
        return {"items": [coerce(x) for x in docs]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
