import {useEffect,useRef,useState} from "react";
import {Check,Copy,MessageSquareText} from "lucide-react";
import {Button} from "@/components/ui/button";
import type {Resource} from "@/lib/types";

type Props={matches:Resource[]; question:string; topics:Record<string,string|undefined>};
export function OfficeDraft({matches,question,topics}:Props) {
  const [picked,setPicked]=useState(matches[0]?.id||"");
  const [created,setCreated]=useState(false),[text,setText]=useState(""),[busy,setBusy]=useState(false),[copied,setCopied]=useState(false),[error,setError]=useState("");
  const textarea=useRef<HTMLTextAreaElement>(null), request=useRef(0);
  const target=matches.find(r=>r.id===picked)||matches[0];
  useEffect(()=>()=>{request.current++;},[]);
  function reset(id:string) {request.current++;setPicked(id);setCreated(false);setText("");setCopied(false);setError("");setBusy(false);}
  async function generate() {
    if(!target||busy)return;
    const job=++request.current;
    setBusy(true);setError("");setCopied(false);
    try {
      const {draftQuestion}=await import("@/lib/campus-ai");
      const output=await draftQuestion(target.id,question,topics[target.id]);
      if(job!==request.current)return;
      setCreated(true);setText(output); requestAnimationFrame(()=>textarea.current?.focus());
    } catch {if(job===request.current)setError("The draft couldn't be created. You can still open the office listing above.");}
    finally {if(job===request.current)setBusy(false);}
  }
  async function copy() {
    if(!text.trim())return;
    try {await navigator.clipboard.writeText(text);setCopied(true);}
    catch {textarea.current?.focus();textarea.current?.select();setError("Your draft is selected. Use your usual copy shortcut.");}
  }
  if(!target)return null;
  return <section className="feature-box office-draft" aria-labelledby="office-draft-title">
    <div className="draft-symbol"><MessageSquareText size={21} aria-hidden="true"/></div><div className="small-cap">CONTACT THE OFFICE</div>
    <h2 id="office-draft-title">Draft a follow-up</h2>
    <p>Turn your situation into a short question to ask in person or by email.</p>
    {matches.length>1?<label className="stack-label">Office
      <select className="feature-input" aria-label="Office for the draft" value={target.id} onChange={e=>reset(e.target.value)}>
        {matches.map(r=><option key={r.id} value={r.id}>{r.name}</option>)}
      </select>
    </label>:<p className="draft-recipient">For <strong>{target.name}</strong></p>}
    {!created?<Button type="button" className="draft-generate" variant="outline" disabled={busy} onClick={()=>void generate()}><MessageSquareText size={16}/>{busy?"Drafting…":"Draft a question"}</Button>:
      <><label className="stack-label" htmlFor="office-draft-text">Your draft</label>
        <textarea id="office-draft-text" ref={textarea} className="feature-input" rows={2} maxLength={600} value={text}
          onChange={e=>{setText(e.target.value);setCopied(false);setError("");}}/>
        <div className="feature-actions"><Button type="button" variant="outline" disabled={!text.trim()} onClick={()=>void copy()}>{copied?<Check size={15}/>:<Copy size={15}/>} {copied?"Copied":"Copy draft"}</Button>
        <span className="draft-caption">Edit it before you use it. Nothing is sent.</span></div>
      </>}
    <div className="draft-credit">Drafts are generated on this device with TensorFlow.js.</div>
    {error&&<p className="feature-error" role="status">{error}</p>}
  </section>;
}
