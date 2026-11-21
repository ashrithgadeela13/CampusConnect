import * as tf from "@tensorflow/tfjs-core";
import "@tensorflow/tfjs-backend-cpu";
import weightsUrl from "../ai/browser-model.f32?url&no-inline";
import specUrl from "../ai/browser-model.json?url&no-inline";

interface Shape { shape: number[]; offset: number }
interface Spec {
  format: number;
  aliases: Record<string,string>; stop: string[];
  topics: {id:string; office:string; cues:string[]; allowed:number[]}[]; vocab:string[];
  phrases: Record<string,number[]>; next: Record<string,number[]>; tensors: Record<string,Shape>;
}
type Runtime = {s:Spec; t:Record<string,tf.Tensor>; stop:Set<string>};
let model:Promise<Runtime>|undefined;
async function load():Promise<Runtime> {
  if(!await tf.setBackend("cpu")) throw new Error("The local model could not start.");
  await tf.ready();
  const [spec,weights]=await Promise.all([fetch(specUrl),fetch(weightsUrl)]);
  if(!spec.ok || !weights.ok) throw new Error("Could not open the local model.");
  const s:Spec=await spec.json(), bytes=new Float32Array(await weights.arrayBuffer());
  if(s.format!==2) throw new Error("Unrecognized campus model.");
  const t:Record<string,tf.Tensor>={};
  for (const [key,{offset,shape}] of Object.entries(s.tensors)) {
    const end=offset+shape.reduce((a,b)=>a*b,1);
    if(end>bytes.length) throw new Error("Incomplete campus model.");
    t[key]=tf.tensor(bytes.subarray(offset,end),shape,"float32");
  }
  return {s,t,stop:new Set(s.stop)};
}
function getModel() {
  if(!model) model=load().catch(error=>{model=undefined;throw error;});
  return model;
}
function terms(text:string,r:Runtime) {
  const clean=text.toLowerCase().normalize("NFKD").replace(/[\u0300-\u036f]/g,"")
    .replace(/wi[\s-]*fi/g,"wifi").replace(/i[\s-]*20/g,"i20");
  return (clean.match(/[a-z0-9]+/g)||[]).filter(w=>!r.stop.has(w)).map(w=>r.s.aliases[w]||w);
}
function draftTopic(r:Runtime,office:string,query:string,topicId?:string) {
  const exact=r.s.topics.findIndex(t=>t.office===office&&t.id===topicId);
  if(exact!==-1)return exact;
  const words=new Set(terms(query,r)),indexed=r.s.topics.map((topic,i)=>({topic,i})).filter(x=>x.topic.office===office);
  if(!indexed.length)return r.s.topics.findIndex(t=>t.office==="*");
  return indexed.map(x=>({...x,score:x.topic.cues.reduce((s,w)=>s+(words.has(w)?1:0),0)})).sort((a,b)=>b.score-a.score||a.i-b.i)[0].i;
}
type Beam={words:number[];cost:number;done:boolean};
function merit(b:Beam) {return b.cost/Math.pow(Math.max(1,b.words.length-1),.65);}
const caps:Record<string,string>={i:"I",id:"ID","wi-fi":"Wi-Fi",fablab:"FabLab","3d":"3D",mav:"Mav",netid:"NetID"};
// The decoder produces one word at a time. The training vocabulary and observed word
// transitions constrain it to campus questions. No finished draft is stored in this file.
export async function draftQuestion(office:string,query:string,topicId?:string):Promise<string> {
  const r=await getModel(), s=r.s, topic=draftTopic(r,office,query,topicId), n=s.vocab.length, nt=s.topics.length;
  const allowed=new Set(s.topics[topic].allowed);
  let beams:Beam[]=[{words:[1,1],cost:0,done:false}];
  for(let step=0;step<26;step++) {
    const active=beams.filter(b=>!b.done), pool=beams.filter(b=>b.done);
    if(!active.length)break;
    const ids=active.flatMap(b=>[topic, nt+b.words[b.words.length-2], nt+n+b.words[b.words.length-1]]);
    const logits=tf.tidy(()=>{
      const embedded=tf.gather(r.t.genw,tf.tensor2d(ids,[active.length,3],"int32"));
      const h=tf.relu(tf.add(tf.sum(embedded,1),r.t.genb));
      return Array.from(tf.logSoftmax(tf.add(tf.matMul(h,r.t.geno),r.t.genc)).dataSync());
    });
    active.forEach((b,i)=>{
      const context=[1,...b.words].slice(-3).join(",");
      const possible=(s.phrases[context]||s.next[String(b.words[b.words.length-1])]||[]).filter(k=>allowed.has(k)&&(k!==0||step>=5));
      for(const k of possible)pool.push({words:[...b.words,k],cost:b.cost+logits[i*n+k],done:k===0});
    });
    beams=pool.sort((a,b)=>merit(b)-merit(a)).slice(0,6);
    if(beams.length===0)break;
  }
  const best=beams.filter(b=>b.done).sort((a,b)=>merit(b)-merit(a))[0];
  if(!best)throw new Error("Could not finish this draft. Please try again.");
  const text=best.words.slice(2,-1).map(i=>caps[s.vocab[i]]||s.vocab[i]).join(" ");
  return text.charAt(0).toUpperCase()+text.slice(1)+"?";
}
