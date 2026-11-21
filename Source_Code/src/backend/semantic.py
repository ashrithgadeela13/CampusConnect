"""CPU inference for the published MinishLab/potion-base-8M model; no install step.

Use the model's original WordPiece tokenizer vocabulary and float32 safetensors.
This implements Model2Vec's mean pooling and unit normalization for this checkpoint.
"""
import json
import math
import struct
import unicodedata
from functools import lru_cache

from .db import ROOT

MODEL_DIR = ROOT / "ai" / "potion-base-8M"

def _cjk(cp):
    return any(a <= cp <= b for a, b in ((0x4e00,0x9fff),(0x3400,0x4dbf),
        (0x20000,0x2a6df),(0x2a700,0x2b73f),(0x2b740,0x2b81f),(0x2b820,0x2ceaf),
        (0xf900,0xfaff),(0x2f800,0x2fa1f)))

class PotionEncoder:
    def __init__(self, folder=MODEL_DIR):
        tok = json.loads((folder / "tokenizer.json").read_text(encoding="utf-8"))["model"]
        self.vocab = tok["vocab"]
        self.continuation = tok["continuing_subword_prefix"]
        self.max_word = tok["max_input_chars_per_word"]
        raw = (folder / "model.safetensors").read_bytes()
        n = struct.unpack_from("<Q", raw)[0]
        descriptor = json.loads(raw[8:8+n])["embeddings"]
        rows, self.width = descriptor["shape"]
        start, end = descriptor["data_offsets"]
        if descriptor["dtype"] != "F32" or rows != len(self.vocab) or end-start != rows*self.width*4 or len(raw)!=8+n+end:
            raise ValueError("Invalid Potion embedding table")
        self.data = memoryview(raw)[8+n+start:8+n+end]
        self.row = struct.Struct("<" + "f"*self.width)

    def tokens(self, text):
        clean = []
        for c in text:
            typ = unicodedata.category(c)
            if c in "\t\n\r" or typ=="Zs":
                clean.append(" ")
            elif typ not in ("Cc","Cf") and c!="\ufffd":
                clean.extend((" ",c," ") if _cjk(ord(c)) else (c,))
        stripped = unicodedata.normalize("NFD","".join(clean).lower())
        basic = []
        for c in stripped:
            typ=unicodedata.category(c); cp=ord(c)
            if typ=="Mn": continue
            is_punct=typ.startswith("P") or any(a<=cp<=b for a,b in ((33,47),(58,64),(91,96),(123,126)))
            basic.extend((" ",c," ") if is_punct else (c,))
        ids=[]
        for word in "".join(basic).split():
            if len(word)>self.max_word: continue
            pieces=[]; i=0
            while i<len(word):
                j=len(word)
                while j>i:
                    k=word[i:j] if i==0 else self.continuation+word[i:j]
                    if k in self.vocab:break
                    j-=1
                if j==i:
                    pieces=[];break
                pieces.append(self.vocab[k]); i=j
            ids.extend(pieces)
        return ids

    def encode(self, text):
        ids = self.tokens(text)
        if not ids:return ()
        acc = [0.0] * self.width
        for i in ids:
            row = self.row.unpack_from(self.data, i*self.row.size)
            acc = [a+b for a,b in zip(acc,row)]
        # Sum and mean have the same unit vector.
        norm = math.sqrt(sum(v*v for v in acc))
        return tuple(v/norm for v in acc) if norm else ()

@lru_cache(maxsize=1)
def encoder():
    try: return PotionEncoder()
    except (OSError,ValueError,KeyError,struct.error): return None

def similarity(a,b):
    return sum(x*y for x,y in zip(a,b)) if a and b else 0.0

