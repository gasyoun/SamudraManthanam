from fastapi import APIRouter
from app.services.morph_service import detect_encoding, to_slp1, to_all_encodings, expand_word
from app.settings import settings

router = APIRouter(prefix="/api/morph", tags=["morphology"])

@router.get("/{word}")
async def get_morph(word: str):
    encoding = detect_encoding(word)
    slp1 = to_slp1(word, encoding)
    stems = await expand_word(slp1)
    variants: set = set()
    for s in stems:
        variants.update(to_all_encodings(s))
    return {
        "input": word,
        "encoding": encoding,
        "slp1": slp1,
        "stems": stems,
        "variants": list(variants),
    }
