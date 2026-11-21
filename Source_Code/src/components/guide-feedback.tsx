import {useState} from "react";
import {api,message} from "@/components/client-data";
import {Button} from "@/components/ui/button";

export function GuideFeedback({receipt}:{receipt:string}){
 const [negative,setNegative]=useState(false);
 const [reason,setReason]=useState("");
 const [status,setStatus]=useState<"idle"|"saving"|"saved">("idle");
 const [error,setError]=useState("");
 async function vote(solved:boolean){
   setError("");
   setStatus("saving");
   try {
     await api("/api/guide/feedback",{receipt,solved,reason:solved?"":reason});
     setStatus("saved");
   } catch(e){
     setError(message(e));
     setStatus("idle");
   }
 }
 return <section className="feature-box" aria-label="Find help feedback">
   <h2>Did this solve your problem?</h2>
   {status==="saved"?<p role="status">Thanks for your feedback.</p>:<>
     <div className="feature-actions">
       <Button variant="outline" disabled={status==="saving"} onClick={()=>void vote(true)}>Yes</Button>
       <Button variant="outline" disabled={status==="saving"} aria-expanded={negative} onClick={()=>setNegative(!negative)}>No</Button>
     </div>
     {negative&&<form onSubmit={e=>{e.preventDefault();void vote(false);}}>
       <label className="stack-label">What went wrong? (Optional)
         <select className="feature-input" value={reason} onChange={e=>setReason(e.target.value)} disabled={status==="saving"}>
           <option value="">Choose a reason</option>
           {["Wrong office","Instructions unclear","Couldn't find my service","Other"].map(value=><option key={value}>{value}</option>)}
         </select>
       </label>
       <p>Your question and the suggested offices will be visible to CampusConnect admins.</p>
       <Button type="submit" disabled={status==="saving"}>Send feedback</Button>
     </form>}
     {error&&<p className="feature-error" role="alert">{error}</p>}
   </>}
 </section>;
}
