import {createRoot} from "react-dom/client";
import {useEffect,useState,type FormEvent} from "react";
import {Compass,ArrowRight,ArrowLeft,LockKeyhole,Eye,EyeOff} from "lucide-react";
import {accountReturnHash} from "@/lib/navigation";
import {Brand,CampusIllustration} from "@/components/wayfinding";
import CampusApp from "@/components/campus-app";
import type {Account,Category,Resource} from "@/lib/types";
import "./style.css";
import "./directory-theme.css";
type Boot={account:Account|null;categories:Category[];resources:Resource[]};
function AccountPage({page}:{page:"login"|"register"|"logout"}) {
 const register=page==="register",logout=page==="logout",dest=accountReturnHash();
 const [username,setUsername]=useState(""),[name,setName]=useState(""),[password,setPassword]=useState(""),[show,setShow]=useState(false),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function submit(e:FormEvent){e.preventDefault();if(busy)return;setBusy(true);setError("");try{
  const res=await fetch("/api/auth/"+page,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(logout?{}:register?{username,name,password}:{username,password})});
  const data=await res.json();if(!res.ok)throw Error(data.error||"Please try again.");
  window.location.assign(logout?"/":"/"+dest);
 }catch(e){setError(e instanceof Error?e.message:"Couldn’t reach CampusConnect.");setBusy(false);}}
 useEffect(()=>{document.title=(logout?"Sign out":register?"Create an account":"Sign in")+" | CampusConnect";},[page]);
 return <main className="account-page"><header className="account-header"><Brand/><a href={"/"+dest}><ArrowLeft size={15}/>Back to directory</a></header>
 <div className="account-layout"><aside className="account-intro"><div className="hero-eyebrow"><span/> UT ARLINGTON <b>/</b> STUDENT DIRECTORY</div><h2>Your campus<br/>directory.</h2><p>Keep your go-to offices, contacts, and resources in one place.</p><CampusIllustration/></aside>
 <section className="feature-box auth-box"><div className="small-cap"><LockKeyhole size={15}/> CAMPUSCONNECT ACCOUNT</div><h1>{logout?"Sign out?":register?"Create your account":"Welcome back"}</h1><p>{logout?"Your bookmarks and recent activity will stay in your account.":register?"Create a local student account to bookmark offices and keep track of recent visits.":"Sign in to CampusConnect to access your saved resources."}</p>
 <form onSubmit={submit}>{!logout&&<>{register&&<label className="stack-label" htmlFor="display-name">Display name<input id="display-name" autoComplete="nickname" required minLength={1} maxLength={60} className="feature-input" value={name} onChange={e=>setName(e.target.value)}/></label>}
 <label className="stack-label" htmlFor="account-user">Username<input id="account-user" autoComplete="username" autoCapitalize="none" spellCheck={false} required minLength={3} maxLength={40} className="feature-input" value={username} onChange={e=>setUsername(e.target.value)} aria-describedby={register?"username-hint":undefined}/></label>
 {register&&<small id="username-hint">Use 3–40 characters. Start with a letter or number. Dots, underscores and hyphens are allowed.</small>}
 <label className="stack-label" htmlFor="account-password">Password</label><div className="password-field"><input id="account-password" type={show?"text":"password"} autoComplete={register?"new-password":"current-password"} required minLength={register?12:1} maxLength={128} className="feature-input" value={password} onChange={e=>setPassword(e.target.value)} aria-describedby={register?"password-hint":undefined}/><button type="button" aria-label={show?"Hide password":"Show password"} aria-pressed={show} onClick={()=>setShow(!show)}>{show?<EyeOff size={18}/>:<Eye size={18}/>}</button></div>
 {register&&<small id="password-hint">Use at least 12 characters and a password just for this app.</small>}</>}
 {error&&<p className="feature-error" role="alert">{error}</p>}<button className="auth-primary" disabled={busy} type="submit">{busy?"One moment…":logout?"Sign out":register?"Create student account":"Sign in"} <ArrowRight size={17}/></button></form>
 {!logout&&<p className="auth-switch">{register?"Already have an account? ":"New to CampusConnect? "}<a href={(register?"/login":"/register")+dest}>{register?"Sign in":"Create a student account"}</a></p>}</section></div><p className="account-note">Independent student project at UT Arlington. No university login required.</p></main>;
}
function Directory(){const [state,setState]=useState<Boot|null>(null),[error,setError]=useState(false);useEffect(()=>{const stop=new AbortController();fetch("/api/bootstrap",{cache:"no-store",signal:stop.signal}).then(async r=>{if(!r.ok)throw Error();setState(await r.json());}).catch(()=>{if(!stop.signal.aborted)setError(true);});return()=>stop.abort();},[]);
 if(!state)return <main className="auth-wrap"><div className="brand"><span className="brand-icon"><Compass/></span>CampusConnect</div>{error?<><h1>Couldn’t load the directory.</h1><p>Make sure the CampusConnect launcher is still open, then try again.</p><button className="auth-primary" onClick={()=>location.reload()}>Try again</button></>:<p role="status">Loading campus resources…</p>}</main>;
 return <CampusApp initialAccount={state.account} initialCategories={state.categories} initialResources={state.resources}/>;
}
const path=window.location.pathname.replace(/^\/|\/$/g,"");createRoot(document.getElementById("root")!).render(path==="login"||path==="register"||path==="logout"?<AccountPage page={path}/>:<Directory/>);
