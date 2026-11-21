import type {CSSProperties} from "react";

export function Brand(){return <a className="brand" href="/" aria-label="CampusConnect home"><span className="brand-icon" aria-hidden="true"><svg viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="13" stroke="currentColor" strokeWidth="1.8"/><path d="m27 12-4.3 10.8L13 28l4.4-11z" fill="#ffd18b"/><path d="m27 12-7.4 8.4L13 28l4.4-11z" fill="white"/></svg></span><span>Campus<span className="brand-connect">Connect</span></span></a>}

// An original wayfinding illustration, not a geographic map of the university.
const project=(x:number,y:number,z=0)=>[185+(x-y)*.91, 10+(x+y)*.38-z];
const point=(p:number[])=>p.map(n=>n.toFixed(1)).join(",");
const line=(arr:number[][])=>arr.map((p,i)=>(i?"L":"M")+point(project(p[0],p[1],p[2]??0))).join(" ");
function Block({x,y,w,d,h}:{x:number;y:number;w:number;d:number;h:number}){
 const face=(arr:number[][])=>line(arr)+"Z";
 const front=face([[x,y+d,0],[x+w,y+d,0],[x+w,y+d,h],[x,y+d,h]]), side=face([[x+w,y,0],[x+w,y+d,0],[x+w,y+d,h],[x+w,y,h]]), roof=face([[x,y,h],[x+w,y,h],[x+w,y+d,h],[x,y+d,h]]);
 return <g stroke="#6290a4" strokeWidth=".8" strokeLinejoin="round"><path d={front} fill="#275374"/><path d={side} fill="#183f5d"/><path d={roof} fill="#3a6480"/><path d={face([[x+3,y+3,h+.2],[x+w-3,y+3,h+.2],[x+w-3,y+d-3,h+.2],[x+3,y+d-3,h+.2]])} fill="none" stroke="#7195a8" opacity=".65"/>{Array.from({length:Math.floor((w-5)/6)},(_,i)=><path key={i} d={line([[x+5+6*i,y+d+0.2,h*.38],[x+5+6*i,y+d+0.2,h*.73]])} stroke="#87a6b4" strokeWidth="1.6"/>)}{Array.from({length:Math.floor((d-5)/7)},(_,i)=><path key={i} d={line([[x+w+.2,y+5+7*i,h*.38],[x+w+.2,y+5+7*i,h*.73]])} stroke="#638aa1" strokeWidth="1.6"/>)}</g>;
}
const buildings=[[8,10,32,20,9],[58,5,43,19,12],[127,8,30,25,11],[170,15,40,20,13],[16,59,30,32,16],[72,53,33,24,17],[129,62,47,23,23],[186,61,29,27,10],[2,125,35,18,10],[52,115,32,21,12],[98,116,36,22,11],[150,118,36,21,10],[204,116,27,18,9]];
export function CampusIllustration({className=""}:{className?:string}){
 const route=[[4,107],[61,107],[61,88],[116,88],[116,45],[169,45]];const end=project(169,45);const start=project(4,107);
 return <svg className={"campus-illustration "+className} viewBox="38 -7 385 170" aria-hidden="true" focusable="false" fill="none" style={{"--map-color":"#5d8792"} as CSSProperties}>
 <g stroke="#547c8a" strokeWidth=".8" opacity=".58">{[0,49,111,178,239].map(x=><path key={x} d={line([[x,-15],[x,150]])}/>)}{[0,42,101,146].map(y=><path key={y} d={line([[-15,y],[250,y]])}/>)}</g>
 <g stroke="#537888" strokeWidth="1.4" fill="#244f63">{[[48,43],[99,91],[179,108],[15,109],[205,41],[132,39],[33,148],[82,22],[196,145]].map(([x,y],i)=>{const p=project(x,y);return <g key={i}><path d={line([[x,y,0],[x,y,7]])}/><ellipse cx={p[0]} cy={p[1]-7} rx="2.8" ry="4.1"/></g>})}</g>
 {buildings.map(([x,y,w,d,h],i)=><Block key={i} {...{x,y,w,d,h}}/>)}<path d={line(route)} stroke="#102e47" strokeWidth="6" strokeLinejoin="round" strokeLinecap="round"/><path d={line(route)} stroke="#efbc74" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="4 4"/><circle cx={start[0]} cy={start[1]} r="4" fill="#183e59" stroke="#ffd390" strokeWidth="2"/>
 <g transform={`translate(${end[0]} ${end[1]})`}><ellipse rx="12" ry="4" fill="#102f49" stroke="#cca66e" strokeWidth=".8"/><path d="M0 -1C-2 -5 -10 -12 -10 -19A10 10 0 1 1 10 -19C10 -12 2 -5 0 -1Z" fill="#ffd191" stroke="#172f44" strokeWidth="1.3"/><circle cy="-19" r="3.1" fill="#20445e"/></g></svg>;
}
