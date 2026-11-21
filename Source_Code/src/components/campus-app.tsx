"use client";

import {useCallback,useEffect,useMemo,useRef,useState,type FormEvent,type CSSProperties} from "react";
import {ArrowUpRight,ArrowRight,Search,MapPin,Clock,Mail,Phone,GraduationCap,Wallet,BriefcaseBusiness,Monitor,HeartPulse,Accessibility,Globe,Compass,LayoutGrid,Settings2,Plus,Archive,RotateCcw,Pencil,LogOut,ChevronDown,ShieldCheck,UserRound,LoaderCircle,X,Check,ExternalLink,SlidersHorizontal,BookOpen,Bookmark,History,Bell,Tags,ChartColumn,Home,Bus,Flag,ListTree} from "lucide-react";
import type {Account,Category,Resource} from "@/lib/types";
import {matchesResource} from "@/lib/validation";
import {Button} from "@/components/ui/button";
import {Input} from "@/components/ui/input";
import {Textarea} from "@/components/ui/textarea";
import {Dialog,DialogContent,DialogHeader,DialogTitle,DialogDescription} from "@/components/ui/dialog";
import {Sheet,SheetContent,SheetHeader,SheetTitle,SheetDescription} from "@/components/ui/sheet";
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from "@/components/ui/select";
import {AlertDialog,AlertDialogContent,AlertDialogHeader,AlertDialogTitle,AlertDialogDescription,AlertDialogFooter,AlertDialogCancel,AlertDialogAction} from "@/components/ui/alert-dialog";
import {DropdownMenu,DropdownMenuContent,DropdownMenuItem,DropdownMenuSeparator,DropdownMenuTrigger} from "@/components/ui/dropdown-menu";
import {SidebarProvider,Sidebar,SidebarHeader,SidebarContent,SidebarGroup,SidebarGroupLabel,SidebarMenu,SidebarMenuItem,SidebarMenuButton,SidebarFooter,SidebarInset,SidebarTrigger,useSidebar} from "@/components/ui/sidebar";
import {Table,TableBody,TableCell,TableHead,TableHeader,TableRow} from "@/components/ui/table";
import {Toaster,toast} from "sonner";
import {Empty,EmptyHeader,EmptyTitle,EmptyDescription} from "@/components/ui/empty";

import {Brand,CampusIllustration} from "@/components/wayfinding";
import {pageLabels,readRoute,routeHash,type Area} from "@/lib/navigation";
import {DirectoryResults} from "@/components/directory-results";
import {useDirectorySearch} from "@/hooks/use-directory-search";
import {useWindowReturn} from "@/hooks/use-window-return";
import {UnansweredPanel} from "@/components/unanswered-panel";
import {GuidePanel} from "@/components/guide-panel";
import {NoticePanel,CategoryPanel,AnalyticsPanel,FeatureHeading} from "@/components/management-panels";
import {api,message} from "@/components/client-data";
import type {Personal} from "@/lib/services";

const icons:Record<string,typeof Compass>={wallet:Wallet,graduation:GraduationCap,briefcase:BriefcaseBusiness,monitor:Monitor,heart:HeartPulse,accessibility:Accessibility,globe:Globe,book:BookOpen,home:Home,bus:Bus,flag:Flag};
const blankForm={category_id:"",name:"",summary:"",description:"",location:"",hours:"",email:"",phone:"",url:"",tags:"",next_steps:"",status:"published" as "published"|"archived",source_checked_on:""};
type ResourceForm=typeof blankForm;
async function requestJson(url:string,init?:RequestInit){
 const response=await fetch(url,init);const data=await response.json() as {error?:string;resources:Resource[];resource:Resource;account:Account};
 if(!response.ok)throw new Error(data.error||"Something went wrong. Please try again.");return data;
}
function focusedControl(){
 const el=document.activeElement;
 return el instanceof HTMLElement&&el!==document.body?el:null;
}
function returnToControl(el:HTMLElement|null){
 (el?.isConnected?el:document.getElementById("main-content"))?.focus({preventScroll:true});
}
function CategoryIcon({name,color,size=20}:{name:string;color?:string;size?:number}){const Icon=icons[name]??Compass;return <Icon size={size} color={color} strokeWidth={1.7}/>;}
function dateLabel(date:string){return date?new Date(date.slice(0,10)+"T12:00:00").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric"}):"Not recorded";}

export default function CampusApp(props:{initialAccount:Account|null;initialCategories:Category[];initialResources:Resource[]}){
 return <SidebarProvider style={{"--sidebar-width":"16.5rem"} as CSSProperties}><CampusWorkspace {...props}/><Toaster richColors position="bottom-right"/></SidebarProvider>;
}
function CampusWorkspace({initialAccount,initialCategories:seedCategories,initialResources}:{initialAccount:Account|null;initialCategories:Category[];initialResources:Resource[]}){
 const [account,setAccount]=useState(initialAccount),[resources,setResources]=useState(initialResources);
 const [initialCategories,setCategories]=useState(seedCategories);
 const [lists,setLists]=useState<Personal>({saved:[],recent:[]}),[listError,setListError]=useState(""),[listLoading,setListLoading]=useState(!!initialAccount),[savingList,setSavingList]=useState(false),[clearing,setClearing]=useState(false);
 const detailOpener=useRef<HTMLElement|null>(null),formOpener=useRef<HTMLElement|null>(null),detailToForm=useRef(false);
 const lastSearch=useRef(""),personalPending=useRef(0),directoryRequest=useRef(0);
 const [directoryVisit,setDirectoryVisit]=useState(0),[guideSeed,setGuideSeed]=useState("");
 const [entry]=useState(()=>readRoute(window.location.hash,initialAccount?.effectiveRole==="admin"));
 const initialCat=seedCategories.some(c=>c.id===entry.category)?entry.category:"all";
 const [view,setView]=useState<Area>(entry.view),[category,setCategory]=useState(initialCat),[query,setQuery]=useState("");
 const [status,setStatus]=useState("published"),[detailId,setDetailId]=useState<string|null>(entry.office),[editId,setEditId]=useState<string|null>(null);
 const [formOpen,setFormOpen]=useState(false),[form,setForm]=useState<ResourceForm>({...blankForm,category_id:initialCategories[0]?.id??""});
 const [formError,setFormError]=useState(""),[saving,setSaving]=useState(false),[busy,setBusy]=useState(false),[pendingArchive,setPendingArchive]=useState<Resource|null>(null);
 const {setOpenMobile}=useSidebar();
 const isAdmin=account?.effectiveRole==="admin";
 const published=resources.filter(r=>r.status==="published");
 const selected=resources.find(r=>r.id===detailId&&(isAdmin||r.status==="published"));
 const semantic=useDirectorySearch(query,category,resources,view==="directory");
 const managementRows=useMemo(()=>resources.filter(r=>(view==="manage"&&isAdmin?(status==="all"||r.status===status):r.status==="published")&&(category==="all"||r.category_id===category)&&matchesResource(r,query)),[resources,view,isAdmin,status,category,query]);
 const visible=view==="directory"?semantic.rows:managementRows;
 const categoryName=initialCategories.find(c=>c.id===category)?.name;
 const personalArea=view==="saved"||view==="recent";
 const special=!(view==="directory"||view==="manage");
 const lastBase=useRef({view,category});
 function address(v:Area,c:string,office:string|null=null,replace=false,sheet=false){
  const hash=routeHash(v,c,office);if(window.location.hash===hash)return;
  window.history[replace?"replaceState":"pushState"]({campusSheet:sheet},"",hash);
 }
 function navigate(next:Area,cat="all",seed=""){
  if(next==="directory")setDirectoryVisit(n=>n+1);
  address(next,cat);lastBase.current={view:next,category:cat};setView(next);setCategory(cat);setDetailId(null);
  setQuery("");setGuideSeed(seed);setClearing(false);setOpenMobile(false);window.scrollTo({top:0,behavior:"instant"});
 }
 function filterCategory(cat:string){address(view,cat);lastBase.current={view,category:cat};setCategory(cat);}
 function closeDetail(){
  setDetailId(null);
  if(window.history.state?.campusSheet)window.history.back();else address(view,category,null,true);
 }
 useEffect(()=>{
  const restore=()=>{
   if(window.location.hash==="#main-content")return;
   const r=readRoute(window.location.hash,isAdmin);
   const c=initialCategories.some(x=>x.id===r.category)?r.category:"all";
   if(lastBase.current.view!==r.view||lastBase.current.category!==c){
    if(r.view==="directory")setDirectoryVisit(n=>n+1);
    setView(r.view);setCategory(c);setQuery("");setGuideSeed("");setOpenMobile(false);setClearing(false);
    window.scrollTo({top:0,behavior:"instant"});
   }
   lastBase.current={view:r.view,category:c};setDetailId(r.office);
  };
  window.addEventListener("popstate",restore);window.addEventListener("hashchange",restore);
  return ()=>{window.removeEventListener("popstate",restore);window.removeEventListener("hashchange",restore);};
 },[isAdmin,initialCategories,setOpenMobile]);
 useEffect(()=>{
  if(!detailId||selected)return;
  address(view,category,null,true);
  setDetailId(null);
  toast.info("This resource is no longer available.",{id:"unavailable-resource",description:"You can still search for another campus office."});
 },[detailId,selected,view,category]);
 useEffect(()=>{document.title=(selected?.name||categoryName||pageLabels[view])+" | CampusConnect";},[view,categoryName,selected?.name]);
 async function loadPersonal(){if(!account)return;const key=++personalPending.current;setListLoading(true);setListError("");try{const p=await api<Personal>("/api/personal");if(personalPending.current===key)setLists(p);}catch(e){if(personalPending.current===key)setListError(message(e));}finally{if(personalPending.current===key)setListLoading(false);}}
 useEffect(()=>{if(account)void loadPersonal();else{setLists({saved:[],recent:[]});setListLoading(false);}return()=>{personalPending.current++;};},[account?.id]);
 useEffect(()=>{if(!query.trim()||view!=="directory"){lastSearch.current="";return;}if(semantic.searching)return;const key=category+":"+query.trim();const timer=setTimeout(()=>{if(lastSearch.current===key)return;lastSearch.current=key;void api("/api/activity",{kind:"search",found:visible.length>0}).catch(()=>{});},750);return()=>clearTimeout(timer);},[query,category,view,visible.length,semantic.searching]);
 function openDetail(id:string){detailOpener.current=focusedControl();address(view,category,id,false,true);setDetailId(id);const r=resources.find(r=>r.id===id);if(!r||r.status!=="published")return;void api("/api/activity",{kind:"view",id}).then(()=>{if(account)setLists(p=>({...p,recent:[id,...p.recent.filter(x=>x!==id)].slice(0,20)}));}).catch(e=>{if(account)toast.error("Could not update recent activity: "+message(e));});}
 async function bookmark(id:string){if(!account||savingList)return;setSavingList(true);try{const saved=!lists.saved.includes(id);setLists(await api<Personal>("/api/personal",{action:"save",id,saved}));toast.success(saved?"Resource saved":"Bookmark removed");}catch(e){toast.error(message(e));}finally{setSavingList(false);}}
 async function clearRecent(){if(!account||savingList)return;setSavingList(true);try{setLists(await api<Personal>("/api/personal",{action:"clearRecent"}));setClearing(false);toast.success("Recent activity cleared");}catch(e){toast.error(message(e));}finally{setSavingList(false);}}
 function saveButton(r:Resource,large=false){return account?<button className={large?"detail-bookmark":"bookmark-button"} disabled={savingList||listLoading} aria-pressed={lists.saved.includes(r.id)} aria-label={(lists.saved.includes(r.id)?"Remove bookmark for ":"Save ")+r.name} title={lists.saved.includes(r.id)?"Remove bookmark":"Save resource"} onClick={()=>void bookmark(r.id)}><Bookmark size={large?18:16} fill={lists.saved.includes(r.id)?"currentColor":"none"}/>{large&&(lists.saved.includes(r.id)?"Saved to bookmarks":"Save resource")}</button>:large?<a className="detail-bookmark" href={"/login"+routeHash(view,category,detailId)} target="_top"><Bookmark size={17}/>Sign in to save</a>:null;}
 const listRows=(view==="saved"?lists.saved:lists.recent).map(id=>published.find(r=>r.id===id)).filter((r):r is Resource=>!!r);
 function nav(key:Area,label:string,Icon:typeof Compass){return <SidebarMenuItem key={key}><SidebarMenuButton className="nav-item" aria-current={view===key?"page":undefined} isActive={view===key} onClick={()=>navigate(key)}><Icon/><span>{label}</span></SidebarMenuButton></SidebarMenuItem>;}

 const reload=useCallback(async()=>{
  const request=++directoryRequest.current;
  const snapshot=await api<{account:Account|null;categories:Category[];resources:Resource[]}>("/api/bootstrap");
  if(request!==directoryRequest.current)return;
  setAccount(snapshot.account);setCategories(snapshot.categories);setResources(snapshot.resources);
  setCategory(current=>current==="all"||snapshot.categories.some(c=>c.id===current)?current:"all");
 },[]);
 const refreshOnReturn=useCallback(()=>{void reload().catch(()=>{/* Keep the last usable directory; manual Refresh can retry. */});},[reload]);
 useWindowReturn(refreshOnReturn,!isAdmin);
 async function refresh(){setBusy(true);try{await reload();toast.success("Directory refreshed");}catch(e){toast.error((e as Error).message);}finally{setBusy(false);}}
 async function setMode(mode:"student"|"admin"){
  setBusy(true);try{const data=await requestJson("/api/account/mode",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mode})});setAccount(data.account);navigate("directory");setDetailId(null);await reload();toast.success(mode==="student"?"Student preview enabled":"Administrator view restored");}catch(e){toast.error((e as Error).message);}finally{setBusy(false);}
 }
 function openForm(resource?:Resource){
  detailToForm.current=!!detailId;formOpener.current=detailId?detailOpener.current:focusedControl();
  if(detailId)address(view,category,null,true);setDetailId(null);setEditId(resource?.id??null);setForm(resource?Object.fromEntries(Object.keys(blankForm).map(k=>[k,resource[k as keyof Resource]])) as ResourceForm:{...blankForm,category_id:initialCategories[0]?.id??""});setFormError("");setFormOpen(true);
 }
 async function saveResource(event:FormEvent){
  event.preventDefault();if(saving)return;setSaving(true);setFormError("");
  try{const existing=resources.find(r=>r.id===editId);const data=await requestJson(editId?`/api/resources/${editId}`:"/api/resources",{method:editId?"PATCH":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({...form,...(existing?{version:existing.version}:{})})});setResources(old=>[...old.filter(r=>r.id!==data.resource.id),data.resource]);setFormOpen(false);toast.success(data.resource.status==="archived"?"Resource saved to Archived":existing?.status==="archived"?"Resource published to the student directory":editId?"Resource updated":"Resource added");}catch(e){setFormError((e as Error).message);}finally{setSaving(false);}
 }
 async function toggleArchived(r:Resource){
  setSaving(true);try{const data=await requestJson(`/api/resources/${r.id}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({...r,status:r.status==="published"?"archived":"published"})});setResources(old=>old.map(item=>item.id===r.id?data.resource:item));setPendingArchive(null);if(detailId)address(view,category,null,true);setDetailId(null);toast.success(data.resource.status==="archived"?"Resource archived":"Resource restored");}catch(e){toast.error((e as Error).message);}finally{setSaving(false);}
 }
 const field=(key:keyof ResourceForm,value:string)=>setForm(f=>({...f,[key]:value}));
 return <>
  <a className="skip-link" href="#main-content" onClick={e=>{e.preventDefault();document.getElementById("main-content")?.focus();}}>Skip to content</a>
  <Sidebar className="campus-sidebar" role="complementary" aria-label="CampusConnect sidebar">
   <SidebarHeader className="brand-header"><Brand/><span className="campus-label">UT Arlington <span>Student resources</span></span></SidebarHeader>
   <SidebarContent>
    <SidebarGroup className="nav-group"><SidebarMenu>
     <SidebarMenuItem><SidebarMenuButton className="nav-item" aria-current={view==="directory"&&category==="all"?"page":undefined} isActive={view==="directory"&&category==="all"} onClick={()=>navigate("directory")}><LayoutGrid/><span>Resource directory</span><span className="nav-count">{published.length}</span></SidebarMenuButton></SidebarMenuItem>
     {nav("guide","Find help",Compass)}{nav("saved","Bookmarks",Bookmark)}{nav("recent","Recent activity",History)}{nav("notices","Notice board",Bell)}
     {isAdmin&&<><li className="subnav-title">ADMINISTRATION</li>{nav("manage","Manage resources",Settings2)}{nav("categories","Categories",Tags)}{nav("analytics","Usage analytics",ChartColumn)}{nav("unanswered","Unanswered questions",Flag)}</>}
    </SidebarMenu></SidebarGroup>
    <SidebarGroup className="category-nav"><SidebarGroupLabel className="nav-section-label">BROWSE BY NEED</SidebarGroupLabel><SidebarMenu>{initialCategories.map(c=><SidebarMenuItem key={c.id}><SidebarMenuButton className="category-nav-item" aria-current={view==="directory"&&category===c.id?"page":undefined} isActive={view==="directory"&&category===c.id} onClick={()=>navigate("directory",c.id)}><CategoryIcon name={c.icon}/><span>{c.name}</span></SidebarMenuButton></SidebarMenuItem>)}</SidebarMenu></SidebarGroup>

   </SidebarContent>
   <SidebarFooter className="sidebar-footer"><span className="footer-mark"><GraduationCap size={20}/><span>Student resource directory</span></span><p>Independent UT Arlington student project</p></SidebarFooter>
  </Sidebar>
  <SidebarInset className="campus-main">
   <header className="topbar"><div className="topbar-left"><SidebarTrigger className="sidebar-toggle" aria-label="Open navigation"/><span className="crumb-root">CampusConnect</span><span className="crumb-slash" aria-hidden="true">/</span><span className="crumb-current">{pageLabels[view]}</span></div><div className="topbar-right"><span className="campus-pill"><MapPin size={14}/> Arlington, TX</span>{account?<DropdownMenu><DropdownMenuTrigger asChild><button className="account-button" aria-label="Account menu"><span className="avatar">{account.name.slice(0,1).toUpperCase()}</span><span className="account-text">{account.name.includes("@")?account.name.split("@")[0]:account.name.split(" ")[0]}<small>{account.student_preview?"Student preview":isAdmin?"Administrator":"Student"}</small></span><ChevronDown size={15}/></button></DropdownMenuTrigger><DropdownMenuContent align="end" className="w-60"><div className="account-menu-info"><strong>{account.name}</strong><span>{account.email}</span></div><DropdownMenuSeparator/>{account.role==="admin"&&<DropdownMenuItem disabled={busy} onSelect={()=>void setMode(account.student_preview?"admin":"student")}><UserRound/> {account.student_preview?"Return to administrator":"Preview as a student"}</DropdownMenuItem>}<DropdownMenuItem asChild><a href="/logout" target="_top"><LogOut/> Sign out</a></DropdownMenuItem></DropdownMenuContent></DropdownMenu>:<Button asChild className="signin-button"><a href={"/login"+routeHash(view,category,detailId)} target="_top">Sign in <ArrowUpRight size={16}/></a></Button>}</div></header>
   {account?.student_preview===1&&<div className="preview-banner"><UserRound size={17}/><span>You’re viewing the directory as a student. Editing is disabled.</span><button disabled={busy} onClick={()=>void setMode("admin")}>Return to administrator <ArrowRight size={15}/></button></div>}
   <main id="main-content" className="workspace" tabIndex={-1}>
    {special?<>{view==="guide"?<GuidePanel refreshDirectory={reload} seed={guideSeed} categories={initialCategories} resources={published} open={openDetail} browse={id=>navigate("directory",id)}/>:view==="notices"?<NoticePanel key={account?.effectiveRole||"guest"} admin={isAdmin} categories={initialCategories}/>:view==="categories"&&isAdmin?<CategoryPanel categories={initialCategories} onChange={cats=>{setCategories(cats);void reload().catch(e=>toast.error(message(e)));}}/>:view==="analytics"&&isAdmin?<AnalyticsPanel/>:view==="unanswered"&&isAdmin?<UnansweredPanel/>:personalArea?<><FeatureHeading tag="YOUR DIRECTORY" title={view==="saved"?"Bookmarks":"Recent activity"} body={view==="saved"?"Keep the campus resources you want to come back to.":"Reopen your last 20 distinct resources, most recent first."}/>{!account?<div className="feature-box"><h2>Sign in to see your {view==="saved"?"bookmarks":"activity"}</h2><p>Your saved resources and recent views are private to your account in this copy of CampusConnect.</p><Button asChild><a href={"/login"+routeHash(view,category,detailId)} target="_top">Sign in <ArrowUpRight size={16}/></a></Button></div>:<>{listLoading?<p role="status">Loading your list…</p>:listError?<div className="feature-box" role="alert"><p>{listError}</p><Button onClick={()=>void loadPersonal()}>Try again</Button></div>:listRows.length===0?<div className="feature-box"><h2>{view==="saved"?"No bookmarks yet":"No recent resources yet"}</h2><p>{view==="saved"?"Use the bookmark icon on a resource to keep it here.":"Open a resource from the directory or the guide to add it here."}</p><Button onClick={()=>navigate("directory")}>Explore the directory <ArrowRight size={16}/></Button></div>:<><div className="personal-toolbar"><strong>{listRows.length} {listRows.length===1?"resource":"resources"}</strong>{view==="recent"&&(clearing?<span>Clear your history? <button disabled={savingList} onClick={()=>void clearRecent()}>Yes, clear</button><button onClick={()=>setClearing(false)}>Cancel</button></span>:<button onClick={()=>setClearing(true)}>Clear history</button>)}</div><div className="feature-box personal-box">{listRows.map(r=><div className="personal-row" key={r.id}><button className="match-row" onClick={()=>openDetail(r.id)}><span className="match-mark" style={{background:r.category_color}}/><span><small>{r.category_name}</small><strong>{r.name}</strong><span>{r.summary}</span></span><ArrowUpRight size={17}/></button>{saveButton(r)}</div>)}</div></>}</>}</>:null}</>:<>
    <section className={view==="manage"?"management-head":"directory-hero"} aria-label={view==="manage"?"Manage listings":"Directory search"}>
     {view==="manage"?<div className="page-heading"><div><div className="eyebrow">ADMINISTRATION</div><h1>Manage resources</h1><p>Update office details and choose which listings students can see.</p></div><Button className="add-resource" onClick={()=>openForm()}><Plus size={17}/>Add resource</Button></div>:
       <div className="hero-upper"><div className="hero-copy"><div className="hero-eyebrow"><span/>UT ARLINGTON <b>/</b> STUDENT DIRECTORY</div><h1>{categoryName||"Find your campus office."}</h1><p>{categoryName?"Browse offices and services for this topic.":"Look up an office, check its hours, and plan your visit."}</p></div><CampusIllustration/></div>}
     <div className="search-panel"><div className="search-field"><Search size={21}/><Input aria-label="Search campus resources" value={query} onChange={e=>setQuery(e.target.value)} placeholder={view==="manage"?"Search resource listings":"Search for an office or describe what you need"} maxLength={200}/>{query&&<button onClick={()=>setQuery("")} aria-label="Clear search"><X size={18}/></button>}</div><div className="search-divider"/><Select value={category} onValueChange={filterCategory}><SelectTrigger className="category-select" aria-label="Filter by category"><SlidersHorizontal size={16}/><SelectValue placeholder="All categories"/></SelectTrigger><SelectContent><SelectItem value="all">All categories</SelectItem>{initialCategories.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent></Select></div>
     {view==="directory"&&<div className="quick-needs"><span>Popular topics</span>{[{label:"Financial aid",id:"money"},{label:"Academics",id:"academics"},{label:"Careers",id:"career"}].filter(t=>initialCategories.some(c=>c.id===t.id)).map(c=><button key={c.id} aria-pressed={category===c.id} onClick={()=>filterCategory(category===c.id?"all":c.id)}>{c.label}<ArrowRight size={12} aria-hidden="true"/></button>)}</div>}
    </section>
    {view==="directory"&&<button className="guide-promo" onClick={()=>navigate("guide","all",query)}><span className="promo-icon"><Compass size={23}/></span><span><strong>Not sure which office to choose?</strong><span>Tell the resource guide what you need in your own words.</span></span><span className="promo-action">Find help <ArrowRight size={16}/></span></button>}
    {view==="manage"?<>
     <div className="results-toolbar"><h2>Resource listings<span>{visible.length}</span></h2><div className="toolbar-actions"><Select value={status} onValueChange={setStatus}><SelectTrigger aria-label="Filter by publication status" className="status-select"><SelectValue/></SelectTrigger><SelectContent><SelectItem value="published">Published</SelectItem><SelectItem value="archived">Archived</SelectItem><SelectItem value="all">All statuses</SelectItem></SelectContent></Select><Button variant="ghost" size="icon" disabled={busy} aria-label="Refresh directory" onClick={()=>void refresh()}><RotateCcw size={17} className={busy?"animate-spin":""}/></Button></div></div>
     {visible.length===0?<Empty className="empty-state"><Search size={34}/><EmptyHeader><EmptyTitle>No resources found</EmptyTitle><EmptyDescription>Try a different keyword or choose another category.</EmptyDescription></EmptyHeader><Button variant="outline" onClick={()=>{setQuery("");filterCategory("all");setStatus("published");}}>Clear filters</Button></Empty>:<div className="management-table"><Table><TableHeader><TableRow><TableHead>Resource</TableHead><TableHead>Category</TableHead><TableHead>Status</TableHead><TableHead>Updated</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader><TableBody>{visible.map(r=><TableRow key={r.id}><TableCell><button className="table-resource" onClick={()=>openDetail(r.id)}>{r.name}</button><span className="table-location">{r.location}</span></TableCell><TableCell><span className="category-label" style={{color:r.category_color}}>{r.category_name}</span></TableCell><TableCell><span className={`status-badge ${r.status}`}>{r.status==="published"?"Published":"Archived"}</span></TableCell><TableCell className="table-date">{dateLabel(r.updated_at)}</TableCell><TableCell><div className="row-actions"><Button size="icon" variant="ghost" aria-label={`Edit ${r.name}`} onClick={()=>openForm(r)}><Pencil size={16}/></Button><Button size="icon" variant="ghost" aria-label={`${r.status==="published"?"Archive":"Restore"} ${r.name}`} onClick={()=>r.status==="published"?setPendingArchive(r):void toggleArchived(r)} disabled={saving}>{r.status==="published"?<Archive size={16}/>:<RotateCcw size={16}/>}</Button></div></TableCell></TableRow>)}</TableBody></Table></div>}
    </>:<DirectoryResults
      key={JSON.stringify([directoryVisit,category,query.trim().toLowerCase()])}
      resources={visible} searching={semantic.searching} fallback={semantic.fallback} home={category==="all"&&!query.trim()}
      headline={query.trim()?"Search results":categoryName?"Resources in this category":"Explore campus resources"}
      busy={busy} onOpen={openDetail} onRefresh={()=>void refresh()}
      onClear={()=>{setQuery("");filterCategory("all");}} onAsk={query.trim()?()=>navigate("guide","all",query):undefined}
      icon={r=><CategoryIcon name={r.category_icon} color={r.category_color} size={24}/>}
      bookmark={r=>saveButton(r)}
    />}
    <footer className="page-footer"><span><ShieldCheck size={16}/> Resource information links to official university sources.</span><span>Hours can change. Check before you visit.</span></footer>
   </>}</main>
  </SidebarInset>
  <Sheet open={!!selected} onOpenChange={open=>{if(!open)closeDetail();}}><SheetContent onCloseAutoFocus={event=>{
   event.preventDefault();
   if(!detailToForm.current)returnToControl(detailOpener.current);
   detailOpener.current=null;detailToForm.current=false;
  }} className="resource-sheet w-full sm:max-w-[560px] overflow-y-auto p-0">{selected&&<><div className="detail-heading"><span className="resource-icon" style={{color:selected.category_color,background:selected.category_color+"12"}}><CategoryIcon name={selected.category_icon} size={28}/></span><span className="category-label" style={{color:selected.category_color}}>{selected.category_name}</span><SheetHeader className="p-0 gap-3"><SheetTitle className="detail-title">{selected.name}</SheetTitle><SheetDescription className="detail-description">{selected.description}</SheetDescription></SheetHeader></div><div className="detail-body"><h3 className="detail-section-label">Plan your visit</h3><dl className="contact-details"><div><MapPin/><dt>Location</dt><dd>{selected.location}</dd></div><div><Clock/><dt>Hours</dt><dd>{selected.hours}</dd></div>{selected.phone&&<div><Phone/><dt>Phone</dt><dd><a href={`tel:${selected.phone.replace(/[^+\d]/g,"")}`}>{selected.phone}</a></dd></div>}{selected.email&&<div><Mail/><dt>Email</dt><dd><a href={`mailto:${selected.email}`}>{selected.email}</a></dd></div>}</dl>{selected.next_steps&&<section className="next-steps"><h3>Your next steps</h3><ol>{selected.next_steps.split("\n").filter(Boolean).map((step,i)=><li key={i}><span>{i+1}</span>{step}</li>)}</ol></section>}<Button asChild className="official-link"><a href={selected.url} target="_blank" rel="noopener noreferrer">Visit official website <ExternalLink size={17}/></a></Button>{selected.status==="published"&&saveButton(selected,true)}<p className="checked-date">{selected.source_checked_on?"Source reviewed "+dateLabel(selected.source_checked_on)+". ":""}Check the official page for changes.</p>{isAdmin&&<Button variant="outline" className="w-full" onClick={()=>openForm(selected)}><Pencil size={16}/>Edit resource</Button>}</div></>}</SheetContent></Sheet>
  <Dialog open={formOpen} onOpenChange={open=>{if(!saving)setFormOpen(open);}}><DialogContent onCloseAutoFocus={event=>{event.preventDefault();returnToControl(formOpener.current);formOpener.current=null;}} className="resource-form-dialog sm:max-w-[720px] max-h-[92dvh] overflow-y-auto"><DialogHeader><DialogTitle>{editId?"Edit resource":"Add a campus resource"}</DialogTitle><DialogDescription>Use clear details and an official source to help students find the right support.</DialogDescription></DialogHeader><form onSubmit={saveResource} className="resource-form"><label className="full-field">Resource name<Input required minLength={3} maxLength={140} value={form.name} onChange={e=>field("name",e.target.value)}/></label><label>Category<Select value={form.category_id} onValueChange={v=>field("category_id",v)}><SelectTrigger className="w-full" aria-label="Resource category"><SelectValue/></SelectTrigger><SelectContent>{initialCategories.map(c=><SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>)}</SelectContent></Select></label><label>Status<Select value={form.status} onValueChange={v=>field("status",v)}><SelectTrigger className="w-full" aria-label="Resource status"><SelectValue/></SelectTrigger><SelectContent><SelectItem value="published">Published</SelectItem><SelectItem value="archived">Archived</SelectItem></SelectContent></Select></label><label className="full-field">Short description<Input required minLength={10} maxLength={280} value={form.summary} onChange={e=>field("summary",e.target.value)}/></label><label className="full-field">Full description<Textarea required minLength={10} maxLength={2500} rows={3} value={form.description} onChange={e=>field("description",e.target.value)}/></label><label>Location<Input required maxLength={240} value={form.location} onChange={e=>field("location",e.target.value)}/></label><label>Operating hours<Input required maxLength={240} value={form.hours} onChange={e=>field("hours",e.target.value)}/></label><label>Email <span className="optional">optional</span><Input type="email" maxLength={254} value={form.email} onChange={e=>field("email",e.target.value)}/></label><label>Phone <span className="optional">optional</span><Input type="tel" maxLength={60} value={form.phone} onChange={e=>field("phone",e.target.value)}/></label><label className="full-field">Official website<Input type="url" required placeholder="https://www.uta.edu/..." maxLength={600} value={form.url} onChange={e=>field("url",e.target.value)}/></label><label>Search keywords <span className="optional">optional</span><Input maxLength={300} placeholder="tuition, funding, payment" value={form.tags} onChange={e=>field("tags",e.target.value)}/></label><label>Source reviewed on <span className="optional">optional</span><Input type="date" max={new Date().toISOString().slice(0,10)} value={form.source_checked_on} onChange={e=>field("source_checked_on",e.target.value)}/></label><label className="full-field">Next steps <span className="optional">one per line</span><Textarea rows={3} maxLength={1800} value={form.next_steps} onChange={e=>field("next_steps",e.target.value)}/></label>{formError&&<p role="alert" className="form-error full-field">{formError}</p>}<div className="form-actions full-field"><Button type="button" variant="outline" disabled={saving} onClick={()=>setFormOpen(false)}>Cancel</Button><Button type="submit" disabled={saving}>{saving&&<LoaderCircle className="animate-spin" size={16}/>} {saving?"Saving…":editId?"Save changes":"Add resource"}</Button></div></form></DialogContent></Dialog>
  <AlertDialog open={!!pendingArchive} onOpenChange={open=>{if(!open&&!saving)setPendingArchive(null);}}><AlertDialogContent><AlertDialogHeader><AlertDialogTitle>Archive this resource?</AlertDialogTitle><AlertDialogDescription>{pendingArchive?.name} will be hidden from the student directory. You can restore it from the Archived filter.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel disabled={saving}>Cancel</AlertDialogCancel><AlertDialogAction disabled={saving} onClick={e=>{e.preventDefault();if(pendingArchive)void toggleArchived(pendingArchive);}}>{saving?"Archiving…":"Archive resource"}</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
 </>;
}
