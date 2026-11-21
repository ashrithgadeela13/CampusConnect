"""Fit the optional in-browser draft model. The pretrained search model is separate. Python + NumPy are needed only to retrain.
Run: python3 ai/train-browser.py     No held-out questions are read here.
Weights are exported as little-endian float32 tensors for TensorFlow.js.
"""
from pathlib import Path
from collections import defaultdict
import json, re, unicodedata
import numpy as np

ROOT = Path(__file__).resolve().parent
def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))
drafts = read("draft-examples.json")
legacy = read("model.json")
stop, aliases = set(legacy["stop"]), legacy["aliases"]
def terms(text):
    text = "".join(c for c in unicodedata.normalize("NFKD",text.lower()) if not unicodedata.combining(c))
    text = re.sub(r"wi[\s-]*fi","wifi",text)
    text = re.sub(r"i[\s-]*20","i20",text)
    return [aliases.get(w,w) for w in re.findall(r"[a-z0-9]+",text) if w not in stop]
def normalize(v):
    return v / max(float(np.linalg.norm(v)),1e-9)
rng = np.random.default_rng(4821)
def train(x, y, outputs, hidden, epochs, batch, lr, balanced=False):
    # One hidden ReLU layer; softmax cross entropy and Adam updates.
    n, width = x.shape
    weights=[(rng.standard_normal((width,hidden)) * (2/width)**.5).astype("f"),
             np.zeros(hidden,"f"),(rng.standard_normal((hidden,outputs)) * (2/hidden)**.5).astype("f"),np.zeros(outputs,"f")]
    m=[np.zeros_like(w) for w in weights]; v=[np.zeros_like(w) for w in weights]
    sw=1/np.maximum(1,np.bincount(y,minlength=outputs)) if balanced else np.ones(outputs)
    sw=(sw/np.mean(sw[y])).astype("f")
    step=0
    for epoch in range(epochs):
        order=rng.permutation(n)
        for start in range(0,n,batch):
            ix=order[start:start+batch]; xx=x[ix]; yy=y[ix]
            h=np.maximum(0,xx@weights[0]+weights[1]); z=h@weights[2]+weights[3]
            probs=np.exp(z-z.max(axis=1,keepdims=True)); probs/=probs.sum(axis=1,keepdims=True)
            probs[np.arange(len(ix)),yy]-=1; dz=probs*(sw[yy]/len(ix))[:,None]
            dh=(dz@weights[2].T)*(h>0)
            grads=[xx.T@dh+1e-5*weights[0],dh.sum(0),h.T@dz+1e-5*weights[2],dz.sum(0)]
            step+=1
            for j,g in enumerate(grads):
                m[j]=.9*m[j]+.1*g; v[j]=.999*v[j]+.001*g*g
                weights[j]-=lr*(m[j]/(1-.9**step))/(np.sqrt(v[j]/(1-.999**step))+1e-8)
    return weights

def words(q):return re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*",q.lower())
texts=[(t,words(q)) for t,d in enumerate(drafts) for q in d["questions"]]
vocab=["<end>","<start>"]+sorted(set(w for _,ws in texts for w in ws))
wi={w:i for i,w in enumerate(vocab)}; nword=len(vocab); ntopic=len(drafts)
allowed=[set([0]) for d in drafts]; nexts=defaultdict(set); phrases=defaultdict(set); triples=[]; labels=[]
for t,ws in texts:
    older,last2,last=1,1,1
    for w in [wi[w] for w in ws]+[0]:
        triples.append((t,ntopic+last2,ntopic+nword+last)); labels.append(w)
        allowed[t].add(w);nexts[last].add(w);phrases[f"{older},{last2},{last}"].add(w);older,last2,last=last2,last,w
xx=np.zeros((len(triples),ntopic+2*nword),"f");xx[np.arange(len(xx))[:,None],np.array(triples)]=1
gen_arrays=train(xx,np.array(labels),nword,80,150,64,.0045)
spec={"format":2,"aliases":aliases,"stop":sorted(stop),
      "topics":[{"id":d["id"],"office":d["office"],"cues":terms(d["cues"]),"allowed":sorted(a)} for d,a in zip(drafts,allowed)],
      "vocab":vocab,"phrases":{k:sorted(v) for k,v in phrases.items()},"next":{str(k):sorted(v) for k,v in nexts.items()},"tensors":{}}
binary=bytearray()
for prefix,arrays in (("gen",gen_arrays),):
    for key,arr in zip(("w","b","o","c"),arrays):
        arr=np.asarray(arr,dtype="<f4",order="C")
        spec["tensors"][prefix+key]={"offset":len(binary)//4,"shape":list(arr.shape)}
        binary.extend(arr.tobytes())
(ROOT/"browser-model.f32").write_bytes(binary)
(ROOT/"browser-model.json").write_text(json.dumps(spec,separators=(",",":"))+"\n",encoding="utf-8")
print(f"{len(texts)} campus draft examples; {len(triples)} next-word predictions; {len(binary):,} bytes of weights.")
