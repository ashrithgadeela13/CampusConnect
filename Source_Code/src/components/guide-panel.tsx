"use client";
import {useEffect,useRef,useState,type FormEvent} from "react";
import {Compass,ArrowRight,ArrowUpRight,MessageCircle,ListTree,RotateCcw,Check} from "lucide-react";
import {Button} from "@/components/ui/button";
import {api,message} from "@/components/client-data";
import type {Category,Resource} from "@/lib/types";
import {OfficeDraft} from "@/components/office-draft";
import {GuideFeedback} from "@/components/guide-feedback";
import {VoiceQuestion} from "@/components/voice-question";
import type {GuideResult} from "@/lib/classifier";
const examples=["I need to drop a course and take it next semester.","My financial aid didn't come through.","I lost my student ID."];
const tasks:Record<string,string>={"financial-aid":"Understand an award or apply for aid","student-accounts":"Pay a bill or check a refund","money-management":"Build a budget","veterans":"Use military education benefits","registrar":"Request records or resolve registration","academic-advising":"Plan my courses","tutoring":"Get help in a class","writing-center":"Improve a paper or essay","math-clinic":"Work through a math problem","academic-testing":"Register for an exam","career-center":"Find an internship or work on my résumé","interview-room":"Reserve a room for an interview","it-service-desk":"Fix a login, device or Wi-Fi problem","health-services":"Arrange a health appointment","counseling":"Talk to a counselor","student-access":"Request disability accommodations","international-education":"Ask about visa or immigration paperwork","study-abroad":"Study in another country","global-engagement":"Meet students from other cultures","central-library":"Borrow a book or find a study space","fablab":"Make something with a 3D printer","research-lab":"Get help analyzing research data","the-studios":"Record a podcast or edit video","housing-office":"Find a dorm or ask about a housing contract","maverick-pantry":"Get food or basic supplies","parking":"Get a permit or ask about a parking ticket","mavmover":"Find a bus route or stop","mav-card":"Get or replace a student ID","campus-rec":"Use the gym or join an intramural sport","organizations":"Find a club or student group"};
export function GuidePanel({categories,resources,open,browse,refreshDirectory,seed=""}:{refreshDirectory:()=>Promise<void>;categories:Category[];resources:Resource[];open:(id:string)=>void;browse:(id:string)=>void;seed?:string}){
 const [mode,setMode]=useState<"ask"|"steps">("ask"),[question,setQuestion]=useState(seed),[result,setResult]=useState<(GuideResult & {feedbackReceipt:string})|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false),[cat,setCat]=useState(""),[choice,setChoice]=useState("");
 const [chosen,setChosen]=useState("");
 const input=useRef<HTMLTextAreaElement>(null), resultHeading=useRef<HTMLHeadingElement>(null);
 useEffect(()=>{if(result&&mode==="ask")resultHeading.current?.focus({preventScroll:true});},[result,mode]);
 const valid=resources.filter(r=>r.status==="published"),available=categories.filter(c=>valid.some(r=>r.category_id===c.id));
 const options=valid.filter(r=>r.category_id===cat),selected=valid.find(r=>r.id===choice);
 const matched=result?result.resourceIds.map(id=>valid.find(x=>x.id===id)).filter((x):x is Resource=>!!x):[];
 const listingsChanged=!!result&&result.resourceIds.length!==matched.length;
 function edit(){setChosen("");setResult(null);setError("");requestAnimationFrame(()=>input.current?.focus());}
 async function ask(e?:FormEvent){
   e?.preventDefault();if(busy)return;setBusy(true);setError("");setChosen("");
   try {
     const [answer]=await Promise.all([api<GuideResult & {feedbackReceipt:string}>("/api/guide",{question}),refreshDirectory()]);
     setResult(answer);
   }catch(e){setError(message(e));}finally{setBusy(false);}
 }
 function matches(rows:Resource[],lead=false){return <div className="guide-matches">{rows.map((r,i)=><button key={r.id} className={"match-row"+(lead&&i===0?" lead-match":"")} onClick={()=>open(r.id)}>
 <span className="match-mark" style={{background:r.category_color}}/><span><small>{r.category_name}</small><strong>{r.name}</strong><span>{r.summary}</span>{lead&&i===0&&<em>View office details <ArrowRight size={14}/></em>}</span><ArrowRight size={17}/></button>)}</div>;}
 const reasons=new Map(result?.matches.map(m=>[m.id,m]));
 const draftTopics=Object.fromEntries((result?.matches||[]).map(m=>[m.id,m.draft]));
 const clarify=result?.state==="clarify";
 const draftMatches=clarify?matched.filter(r=>r.id===chosen):matched;
 const lead=reasons.get((clarify?chosen:matched[0]?.id)||"");
 return <><div className="page-heading feature-heading"><div><div className="eyebrow"><span/>RESOURCE GUIDE</div><h1>Find help</h1><p>Describe what you need and find an office you can contact.</p></div></div>
 <div className="view-switch guide-tabs" role="group" aria-label="Choose guidance method"><button aria-pressed={mode==="ask"} onClick={()=>setMode("ask")}><MessageCircle size={17}/>Ask a question</button><button aria-pressed={mode==="steps"} onClick={()=>setMode("steps")}><ListTree size={17}/>Step-by-step guide</button></div>
 {mode==="ask"?<>
 {!result?<form className="feature-box ask-form" onSubmit={ask}>
  <div className="ask-fields"><div className="small-cap">YOUR QUESTION</div><h2><label htmlFor="guide-question">What do you need help with?</label></h2>
  <p id="question-guidance">Describe the situation in a sentence. Leave out names, student ID numbers, and other personal details. Questions with no confident match are saved for administrators to review.</p>
  <textarea id="guide-question" ref={input} disabled={busy} className="feature-input" aria-describedby="question-guidance" minLength={3} maxLength={500} required rows={3} placeholder="For example: I lost my student ID. Where can I get a new one?" value={question} onChange={e=>{setQuestion(e.target.value);setError("");}}/>
  <VoiceQuestion disabled={busy} onTranscript={value=>{setQuestion(value);setError("");}}/>
  <Button disabled={busy||question.trim().length<3} type="submit">{busy?"Finding matches…":"Find resources"}<ArrowRight size={16}/></Button></div>
  <aside className="example-panel" aria-label="Example questions"><div className="small-cap">TRY AN EXAMPLE</div>{examples.map(x=><button type="button" disabled={busy} key={x} onClick={()=>{setQuestion(x);setError("");input.current?.focus();}}><span>{x}</span><ArrowRight size={15}/></button>)}</aside>
 </form>:<div className="query-summary"><MessageCircle size={18}/><div><span>Your question</span><p>{question}</p></div><button onClick={edit}>Edit question</button></div>}
 {error&&<p className="feature-error" role="alert">{error}</p>}
 {result&&listingsChanged&&<div className="guide-outcome"><section className="feature-box reveal-box" aria-live="polite">
  <div className="small-cap">DIRECTORY UPDATE</div><h2>These results have changed</h2>
  <p>An office in these results is no longer listed. Search again to see which offices are available.</p>
  <Button disabled={busy} onClick={()=>void ask()}>{busy?"Checking…":"Find current matches"}<ArrowRight size={15}/></Button>
 </section></div>}
 {result&&!listingsChanged&&<div className={"guide-outcome"+(draftMatches.length?" has-draft":"")}>
  <section className="feature-box reveal-box" aria-labelledby="match-heading"><div className="small-cap">{result.state==="match"?"RECOMMENDED OFFICE":result.state==="clarify"?"POSSIBLE MATCHES":"SEARCH RESULT"}</div>
  <h2 id="match-heading" ref={resultHeading} tabIndex={-1}>{result.state==="none"?"No confident match":result.state==="clarify"?"Which office fits your situation?":"A good place to start"}</h2>
  {result.state==="none"?<><p>Try adding the campus service you need, or pick a topic to narrow it down.</p><Button variant="outline" onClick={()=>setMode("steps")}>Try the step-by-step guide <ArrowRight size={15}/></Button></>:
   <>{result.state==="clarify"&&<p>Pick the service you meant. You can then draft a question for that office.</p>}
   {clarify?<div className="service-choices">{matched.map(r=><div className="service-choice" key={r.id}><button className="service-pick" aria-pressed={chosen===r.id} onClick={()=>setChosen(r.id)}><span><strong>{r.name}</strong><small>{reasons.get(r.id)?.label||r.summary}</small></span>{chosen===r.id?<Check size={18}/>:<ArrowRight size={17}/>}</button><button className="quiet-link" onClick={()=>open(r.id)}>Office details <ArrowUpRight size={13}/></button></div>)}</div>:matches(matched.slice(0,1),true)}
   {lead&&<div className="service-reason"><div className="small-cap">MATCHED SERVICE</div><strong>{lead.label}</strong>{lead.detail&&<p>{lead.detail}</p>}{lead.source&&<a href={lead.source.url} target="_blank" rel="noopener noreferrer">{lead.source.label} <ArrowUpRight size={14}/></a>}</div>}
   {!clarify&&matched.length>1&&<><div className="other-matches">Other helpful offices</div>{matches(matched.slice(1))}</>}
   {result.categories.length>0&&<div className="match-topics"><span>Browse by topic</span>{result.categories.map(c=><button key={c.id} onClick={()=>browse(c.id)}>{c.name}<ArrowRight size={12}/></button>)}</div>}</>}
  <details className="match-info"><summary>How matches are chosen</summary><p>{result.method==="model2vec"?<><strong>Pretrained search: Model2Vec (Potion).</strong> The local search model compares the meaning of your words with the services each office handles. CampusConnect also checks office names, keywords and registration guidance.</>:<><strong>Keyword search.</strong> The local model is unavailable, so these results use office names, service descriptions and registration guidance.</>} {result.state==="none"?"The evidence was too weak to recommend an office.":"Office contact details come from published directory listings."}</p></details>
  </section>
  {draftMatches.length>0&&<OfficeDraft key={question+draftMatches.map(r=>r.id).join("/")} matches={draftMatches} question={question} topics={draftTopics}/>}
 </div>}
 {result&&!listingsChanged&&<GuideFeedback key={result.feedbackReceipt} receipt={result.feedbackReceipt}/>}
 </>:<div className="feature-box manual-guide"><div className="small-cap">GUIDED REQUEST <span> / </span>{choice?"RESULT":cat?"STEP 2 OF 2":"STEP 1 OF 2"}</div>
 {!cat?<><h2>What area is this about?</h2><p>Choose the topic closest to what you need.</p><div className="choice-grid">{available.map(c=><button key={c.id} onClick={()=>{setCat(c.id);setChoice("");}}><span className="dot" style={{background:c.color}}/>{c.name}<ArrowRight size={15}/></button>)}</div></>:!choice?<><h2>What would you like to do?</h2><p>{available.find(c=>c.id===cat)?.name} · Choose the closest goal.</p><div className="choice-grid">{options.map(r=><button key={r.id} onClick={()=>{setChoice(r.id);void api("/api/activity",{kind:"guided",id:cat}).catch(()=>{});}}>{tasks[r.id]||r.summary}<ArrowRight size={15}/></button>)}</div><button className="quiet-link" onClick={()=>setCat("")}>Back to topics</button></>:selected?<><h2>Your next stop</h2><p>For “{tasks[selected.id]||selected.summary}”, start here:</p>{matches([selected])}<ol className="steps-list">{selected.next_steps.split("\n").filter(Boolean).map((step,i)=><li key={i}><Check size={15}/>{step}</li>)}</ol><div className="feature-actions"><Button onClick={()=>open(selected.id)}>Open resource <ArrowRight size={16}/></Button><Button variant="outline" onClick={()=>setChoice("")}>Change goal</Button><button className="quiet-link" onClick={()=>{setCat("");setChoice("");}}><RotateCcw size={15}/>Start over</button></div></>:<Button onClick={()=>{setCat("");setChoice("");}}>Start again</Button>}</div>}
 </>;
}
