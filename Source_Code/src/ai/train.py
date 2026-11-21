"""Rebuild the campus vocabulary and IDF weights for the keyword part of search.
Held-out evaluation questions are deliberately not read here.
"""
import json, math, re, unicodedata
from collections import Counter
from pathlib import Path
root = Path(__file__).resolve().parent
stop = "a an the and or to for of in at on with my me i is are can do does how where who it this that would need want help what get have has be from am could by about some a".split()
aliases = {"cv":"resume","resumes":"resume","fees":"fee","classes":"class","courses":"course","studying":"study","visas":"visa","books":"book","journals":"journal","loans":"loan","grants":"grant","housing":"housing","appointments":"appointment","accommodations":"accommodation","internships":"internship","tickets":"ticket","wireless":"wifi","clinics":"clinic"}
def tokens(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii","ignore").decode().lower()
    value = re.sub(r"wi[\s-]*fi","wifi",value)
    value = re.sub(r"i[\s-]*20","i20",value)
    words=[aliases.get(w,w) for w in re.findall(r"[a-z0-9]+",value) if w not in stop]
    return words+[a+"_"+b for a,b in zip(words,words[1:])]
labels=json.loads((root/"training.json").read_text())
docs=[(c,tokens(q)) for c,qs in labels.items() for q in qs]
df=Counter(term for _,words in docs for term in set(words))
idf={term:round(math.log((1+len(docs))/(1+n))+1,7) for term,n in sorted(df.items())}
model={"version":2,"documents":len(docs),"stop":stop,"aliases":aliases,"idf":idf}
(root/"model.json").write_text(json.dumps(model,separators=(",",":"))+"\n")
print(f"keyword weights from {len(docs)} questions in {len(labels)} categories; {len(idf)} terms")
