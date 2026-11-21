import {useEffect,useMemo,useState} from "react";
import type {Resource} from "@/lib/types";
import {matchesResource} from "@/lib/validation";

type ResponseState={key:string;catalog:Resource[];ids:string[]|null;failed:boolean};
export function useDirectorySearch(query:string,category:string,resources:Resource[],enabled:boolean) {
  const term=query.trim(), key=category+"\n"+term;
  const active=enabled&&term.length>=2;
  const [answer,setAnswer]=useState<ResponseState|null>(null);
  useEffect(()=>{
    if(!active)return;
    const controller=new AbortController();
    const wait=window.setTimeout(async()=>{
      try{
        const response=await fetch("/api/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:term,category:category==="all"?"":category}),cache:"no-store",signal:controller.signal});
        if(!response.ok)throw new Error("Search unavailable");
        const data=await response.json() as {resourceIds:string[]};
        if(!controller.signal.aborted)setAnswer({key,catalog:resources,ids:data.resourceIds,failed:false});
      }catch{if(!controller.signal.aborted)setAnswer({key,catalog:resources,ids:null,failed:true});}
    },200);
    return()=>{window.clearTimeout(wait);controller.abort();};
  },[active,term,category,key,resources]);
  const current=active&&answer?.key===key&&answer.catalog===resources?answer:null;
  const rows=useMemo(()=>{
    const allowed=resources.filter(r=>r.status==="published"&&(category==="all"||r.category_id===category));
    if(!current?.ids)return term?allowed.filter(r=>matchesResource(r,term)):allowed;
    const byId=new Map(allowed.map(r=>[r.id,r]));
    return current.ids.map(id=>byId.get(id)).filter((r):r is Resource=>!!r);
  },[resources,category,term,current]);
  return {rows,searching:active&&!current,fallback:!!current?.failed};
}
