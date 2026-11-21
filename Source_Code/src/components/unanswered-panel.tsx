import {useEffect,useState} from "react";
import {api,message} from "@/components/client-data";
import {FeatureHeading} from "@/components/management-panels";
import {Button} from "@/components/ui/button";

type Report={
 counts:{yes:number;no:number;noMatch:number};
 items:{id:string;question:string;outcome:string;offices:string[];reason:string;solved:0|null;created_at:string;reviewed_at:string|null}[];
 hasMore:boolean;
};

export function UnansweredPanel(){
 const [page,setPage]=useState(0);
 const [revision,setRevision]=useState(0);
 const [report,setReport]=useState<Report|null>(null);
 const [error,setError]=useState("");
 const [pending,setPending]=useState("");
 useEffect(()=>{
   let active=true;
   setError("");
   setReport(null);
   api<Report>("/api/admin/unanswered?page="+page)
     .then(result=>{if(active)setReport(result);})
     .catch(e=>{if(active)setError(message(e));});
   return ()=>{active=false;};
 },[page,revision]);

 async function review(id:string,reviewed:boolean){
   setPending(id);
   setError("");
   try {
     await api("/api/admin/unanswered",{id,reviewed});
     setRevision(value=>value+1);
   } catch(e){setError(message(e));}
   finally{setPending("");}
 }
 return <>
   <FeatureHeading tag="ADMINISTRATION" title="Unanswered questions" body="Review searches with no confident match and student reports that Find help did not solve their problem."/>
   {error&&<p className="feature-error" role="alert">{error}</p>}
   {!report&&(!error?<p role="status">Loading questions…</p>:<Button onClick={()=>setRevision(value=>value+1)}>Try again</Button>)}
   {report&&<>
     <div className="feature-box">
       <h2>Feedback totals</h2>
       <p>Yes: {report.counts.yes} · No: {report.counts.no} · No confident match: {report.counts.noMatch}</p>
     </div>
     {report.items.length===0&&<p>No unresolved questions on this page.</p>}
     {report.items.map(item=><article className="feature-box" key={item.id}>
       <div className="small-cap">{item.outcome==="none"?"NO CONFIDENT MATCH":"STUDENT REPORTED UNSOLVED"} · {item.reviewed_at?"REVIEWED":"NEEDS REVIEW"}</div>
       <h2 style={{overflowWrap:"anywhere"}}>{item.question}</h2>
       <p>{new Date(item.created_at).toLocaleString()}</p>
       {item.offices.length>0&&<p>Suggested offices: {item.offices.join(", ")}</p>}
       {item.solved===0&&<p>Student feedback: No{item.reason?" · "+item.reason:""}</p>}
       <Button variant="outline" disabled={!!pending} onClick={()=>void review(item.id,!item.reviewed_at)}>
         {pending===item.id?"Saving…":item.reviewed_at?"Reopen":"Mark reviewed"}
       </Button>
     </article>)}
     {(page>0||report.hasMore)&&<div className="feature-actions">
       <Button variant="outline" disabled={page===0||!!pending} onClick={()=>setPage(value=>value-1)}>Previous</Button>
       <span>Page {page+1}</span>
       <Button variant="outline" disabled={!report.hasMore||!!pending} onClick={()=>setPage(value=>value+1)}>Next</Button>
     </div>}
   </>}
 </>;
}
