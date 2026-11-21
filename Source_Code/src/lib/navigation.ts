export const pageLabels={directory:"Directory",guide:"Find help",saved:"Bookmarks",recent:"Recent activity",notices:"Notice board",manage:"Manage resources",categories:"Categories",analytics:"Usage analytics",unanswered:"Unanswered questions"} as const;
export type Area=keyof typeof pageLabels;
const key=/^[a-z0-9][a-z0-9_-]{0,100}$/i;
export function routeHash(view:Area,category="all",office:string|null=null){
 const p=new URLSearchParams();if((view==="directory"||view==="manage")&&category!=="all"&&key.test(category))p.set("category",category);
 if(office&&key.test(office))p.set("office",office);
 return "#/"+view+(p.size?"?"+p.toString():"");
}
export function readRoute(hash:string,admin:boolean){
 const m=/^#\/([a-z]+)(?:\?(.*))?$/.exec(hash);
 const requested=m&&Object.prototype.hasOwnProperty.call(pageLabels,m[1])?m[1] as Area:"directory";
 const view:Area=!admin&&["manage","categories","analytics","unanswered"].includes(requested)?"directory":requested;
 const p=new URLSearchParams(m?.[2]||"");const c=p.get("category")||"all";const id=p.get("office")||"";
 return {view,category:(view==="directory"||view==="manage")&&key.test(c)?c:"all",office:key.test(id)?id:null};
}
export function accountReturnHash(){
 if(!window.location.hash.startsWith("#/"))return "";
 const r=readRoute(window.location.hash,true);return routeHash(r.view,r.category,r.office);
}
