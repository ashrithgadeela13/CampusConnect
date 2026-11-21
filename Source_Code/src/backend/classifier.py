"""Rank public services directly, using pretrained Model2Vec vectors and lexical evidence."""
import json
import math
import re
import unicodedata
from collections import Counter
from functools import lru_cache
from .db import ROOT
from .semantic import encoder, similarity

def read(file):
    return json.loads((ROOT / file).read_text(encoding="utf-8"))

LEX = read("ai/model.json")
PROFILES = read("ai/service-intents.json")
SEED = {r["id"]:r["name"].casefold() for r in read("data-source/catalog.json")["resources"]}
STOP = set(LEX["stop"]) | set("would could may should did didn't didn't can't i'm i'd won't it's somewhere anyone someone something anything please hello hey hi thanks thank advise tell figure sure know get getting gets trying want need wants somewhere like really now also have has had do does thing question ll ve im ive who".split())
ALIASES = {**LEX["aliases"],"dropping":"drop","dropped":"drop","withdrawing":"withdraw","withdrawn":"withdraw","withdrawals":"withdraw","withdrawal":"withdraw","budgeting":"budget","budgets":"budget","majors":"major","minutes":"minute","transcripts":"transcript","electives":"elective","modules":"module","professors":"professor","subjects":"subject","retaking":"retake","semester":"term","semesters":"term","spring":"term","fall":"term","retook":"retake","losing":"lost","missing":"missing","renewing":"renew","dorms":"dorm","internet":"wifi"}
STOP |= set("was were isnt haven hasnt hasn wasn couldnt but or which up will already one two getting got just does would take toward did someone campus university really still rather figure out all yet".split())
STOP |= {"s","t","d","re","m","don","didn","doesn","isn","wasn","won","can","cannot","couldn","there","then","myself","my","another","somewhere","someone","people","next"}
def raw_words(s):
    clean=unicodedata.normalize("NFKD",s.casefold())
    clean="".join(c for c in clean if not unicodedata.combining(c))
    clean=re.sub(r"wi[\s-]*fi","wifi",clean)
    clean=re.sub(r"\bi[\s-]*20\b","i20",clean)
    return re.findall(r"[a-z0-9]+",clean)

def parts(s):
    return [w for w in raw_words(s) if w not in STOP]

def normalized(s):
    return " ".join(raw_words(s))

def focus(s):
    # A student may name the wrong service only to rule it out.
    clauses=re.split(r"\s*(?:[;—]|\bbut\b|\binstead\b)\s*",s,flags=re.I)
    if len(clauses)>1 and re.search(r"\b(?:i (?:need|want|would like)|can (?:someone|anyone)|who can|how (?:do|can))\b",clauses[-1],re.I):
        return clauses[-1]
    if len(clauses)>1 and re.search(r"\b(?:not|don't|don’t|isn't|isn’t|rather than)\b",clauses[0],re.I):
        return " ".join(clauses[1:]).strip() or s
    return s

def features(texts):
    # Keep compact word pairs as well as individual terms for office names and campus codes.
    words=[ALIASES.get(w,w) for w in texts]
    cnt=Counter(words+[a+"_"+b for a,b in zip(words,words[1:])])
    values={k:(1+math.log(v))*min(4,max(1,LEX["idf"].get(k,3))) for k,v in cnt.items()}
    norm=math.sqrt(sum(x*x for x in values.values())) or 1
    return {k:v/norm for k,v in values.items()}

def representation(s):
    tokens=parts(s); model=encoder()
    return (model.encode(" ".join(tokens)) if model and tokens else (),features(tokens))

# Only office text and authored service descriptions enter this cache. Never cache student queries.
office_repr=lru_cache(maxsize=1800)(representation)

def compare(query,s,weight=1.0):
    doc,words=office_repr(s)
    sem=max(0,similarity(query[0],doc))
    lex=sum(value*words.get(k,0) for k,value in query[1].items())
    score=(.72*sem+.28*lex) if query[0] else lex
    return (score*weight,sem,lex)

@lru_cache(maxsize=8)
def office_terms(snapshot):
    sets={}
    for rid,name,tags in snapshot:
        profiles=PROFILES.get(rid,()) if SEED.get(rid)==name.casefold() else ()
        cues=[name,tags]+[s for p in profiles for s in (p["label"],*p["phrases"])]
        sets[rid]={ALIASES.get(w,w) for line in cues for w in parts(line)}
    freq=Counter(w for words in sets.values() for w in words)
    return sets,freq

def enrollment_intent(q):
    """A change of enrollment can be an advising, records, aid, billing or visa question."""
    w={ALIASES.get(x,x) for x in raw_words(q)}
    lower=q.casefold()
    if re.search(r"\bdrop[ -]?(?:in|off|box|by)\b|\b(?:grades?|scores?|marks?)\s+(?:(?:have|has|just)\s+)*dropped",lower):return None
    action=w & {"drop","withdraw","unenroll","unregister","defer","postpone","retake","repeat","leave","remove","quit","switch","cancel","discontinue"}
    load_change=bool(re.search(r"reduc\w*|below|fewer|less than|part[- ]time",lower) and w & {"credit","credits","hour","hours","load","full","time"})
    if not (load_change or (action and w & {"class","course","subject","module","section","term","semester","enrollment","classes","courses","credit","credits"})):return None
    if re.search(r"(?:not|never|don.t) (?:want to |plan to )?(?:drop|withdraw|leave|quit)",lower):return None
    if w & {"visa","immigration","i20","f1","sevis"} or "f-1" in lower:return "international-education","immigration"
    if w & {"grant","scholarship","aid","fafsa","loan","loans","pell"}:return "financial-aid","aid-load"
    if w & {"refund","reimbursement","charged","charges","bill","billing","tuition"}:return "student-accounts","billing"
    if w & {"deadline","deadlines","form","forms","calendar","cutoff","procedure","procedures"} or "last day" in lower:return "registrar","registration"
    return "academic-advising","course-change"

def rank(question,resources):
    q=focus(question); query=representation(q)
    if not query[1]:return []
    qname=normalized(q); qw=parts(q); enrollment=enrollment_intent(q)
    if not qw:return []
    found=[]
    live=[r for r in resources if r.get("status","published")=="published"]
    sets,freq=office_terms(tuple((r["id"],r["name"],r["tags"]) for r in live))
    cues={ALIASES.get(w,w) for w in qw} - set("student college class course term university campus help appointment room use find want need check office service time issue".split())
    for r in live:
        if r.get("status","published")!="published":continue
        rid=r["id"]; name=r["name"]; title=normalized(name)
        profiles=PROFILES.get(rid,()) if SEED.get(rid)==name.casefold() else ()
        general={"key":"listing","label":r["summary"],"phrases":[]}
        base=[x for x in (name,r["summary"],r["description"],r["tags"]) if x]
        best=max(compare(query,s,.94 if s==r["description"] else 1.) for s in base)
        selected=general; best_profile=None
        for profile in profiles:
            v=max(compare(query,s) for s in (profile["label"],*profile["phrases"]))
            if best_profile is None or v>best_profile[0]:best_profile=(v,profile)
            if v[0]>best[0]:best,selected=v,profile
        if selected is general and best_profile and best_profile[0][0]>=max(.33,best[0]-.085):
            selected=best_profile[1]
        if enrollment and enrollment[0]==rid:
            intent=next((p for p in profiles if p["key"]==enrollment[1]),None)
            if intent:
                best=(max(.86,best[0]+.15),best[1],best[2]);selected=intent
        score,sem,lex=best
        # Require independent wording from the office's own name, tags or service descriptions.
        # This rescues a useful match expressed in a long sentence without rewarding "campus" or "class".
        uncommon=sorted((freq[w] for w in cues & sets[rid] if freq[w]<=4))
        if uncommon and score>=.235:
            score+=min(.13, .085/(uncommon[0]**.5)+.028*(len(uncommon)>1))
            lex=max(lex,.20 if uncommon[0]<=2 else .15)
        # Exact office names and short directory terms are useful even for a newly created office.
        exact=qname==title or (len(qname)>=3 and re.search(r"\b"+re.escape(title)+r"\b",qname) is not None)
        if exact:score=max(score,1.15)
        elif len(qw)<=2 and len(qname)>=3 and qname in title:score=max(score,.67)
        # No office is selected simply for belonging to the predicted category.
        found.append((score,sem,lex,r,selected,exact))
    return sorted(found,key=lambda x:(-x[0],x[3]["name"].casefold()))

def accepted(row,model):
    score,sem,lex,_,_,exact=row
    return exact or (score>=.34 and (sem>=.49 or lex>=.19 or score>=.85) if model else score>=.20)

def results(question,resources):
    rows=rank(question,resources); model=bool(encoder())
    if not rows or not accepted(rows[0],model):return []
    return [r for r in rows if accepted(r,model)]

def directory_search(question,resources):
    # A directory lookup may have several valid matches. Category filters are applied before ranking.
    rows=results(question,resources)
    if not rows:
        # Preserve ordinary directory searches for a category name or a short partial office name.
        term=normalized(question)
        if len(term)<2:return []
        return [r["id"] for r in resources if r.get("status","published")=="published" and (term in normalized(r["name"]) or term==normalized(r.get("category_name","")))]
    top=rows[0][0]; short=len(parts(question))<=2
    ids=[r[3]["id"] for r in rows if r[0]>=max(.27,top*(.48 if short else .66))]
    term=normalized(question)
    if short:
        ids.extend(r["id"] for r in resources if r.get("status","published")=="published" and term==normalized(r.get("category_name","")) and r["id"] not in ids)
    return ids

def classify(question,categories,resources,neural_hint=None):
    # An older client can still send a topic hint. Decisions are now made at office/service level.
    model=bool(encoder()); by_id={r["id"]:r for r in resources if r.get("status","published")=="published"}
    method="model2vec" if model else "keywords"
    rows=results(question,list(by_id.values()))
    empty={"state":"none","method":method,"resourceIds":[],"categories":[],"matches":[]}
    if not rows:return empty
    best=rows[0]; selected=[best]
    for r in rows[1:]:
        if len(selected)>=3:break
        if r[0]>=max((.32 if len(parts(question))<=2 else .46) if model else .25,best[0]-.12) and r[0]>=best[0]*.80:selected.append(r)
    related=best[4].get("related",[])
    for rid in related:
        if rid not in by_id or any(x[3]["id"]==rid for x in selected):continue
        p=by_id[rid]; selected=selected[:2]+[(0,0,0,p,{"key":"related","label":p["summary"],"phrases":[]},False)]
    if related:
        # A curated companion office is more useful here than a weak third choice.
        selected=[best]+[r for r in selected[1:] if r[3]["id"] in related]
    vague=len(parts(question))<=2
    close=len(selected)>1 and not related and (best[0]-selected[1][0]<(.105 if vague else .048))
    state="clarify" if close and not best[5] else "match"
    matches=[]; seen=set(); topics=[]
    for _,_,_,office,reason,_ in selected:
        rid=office["id"]; cid=office["category_id"]
        detail={k:reason[k] for k in ("label","detail","source","draft") if k in reason}
        if best[4]["key"]=="course-change" and rid=="registrar":
            detail={"label":"The official add/drop and withdrawal procedure","draft":"registrar-drop"}
        matches.append({"id":rid,**detail})
        if cid not in seen:
            seen.add(cid);topics.extend({"id":cid,"name":c["name"]} for c in categories if c["id"]==cid)
    return {"state":state,"method":method,"categories":topics,"resourceIds":[m["id"] for m in matches],"matches":matches}

