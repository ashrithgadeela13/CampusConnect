import {useEffect,useRef,useState} from "react";
import {Mic,Square} from "lucide-react";
import {Button} from "@/components/ui/button";

type Recognition={
 lang:string;
 onresult:((event:{results:ArrayLike<ArrayLike<{transcript:string}>>})=>void)|null;
 onerror:((event:{error:string})=>void)|null;
 onend:(()=>void)|null;
 start:()=>void;
 stop:()=>void;
 abort:()=>void;
};
type SpeechWindow=Window & {
 SpeechRecognition?:new()=>Recognition;
 webkitSpeechRecognition?:new()=>Recognition;
};

export function VoiceQuestion({disabled,onTranscript}:{disabled:boolean;onTranscript:(text:string)=>void}){
 const browser=window as SpeechWindow;
 const Speech=browser.SpeechRecognition??browser.webkitSpeechRecognition;
 const active=useRef<Recognition|null>(null);
 const [listening,setListening]=useState(false);
 const [status,setStatus]=useState("");
 useEffect(()=>{
   if(disabled&&active.current)active.current.abort();
 },[disabled]);
 useEffect(()=>()=>{
   const recognition=active.current;
   active.current=null;
   if(recognition){
     recognition.onend=recognition.onerror=recognition.onresult=null;
     recognition.abort();
   }
 },[]);
 if(!Speech)return <p className="feature-muted">Voice input is unavailable in this browser. You can type your question.</p>;
 const Recognition=Speech;
 function toggle(){
   if(active.current){
     active.current.stop();
     return;
   }
   const recognition=new Recognition();
   active.current=recognition;
   recognition.lang="en-US";
   let received=false;
   recognition.onresult=event=>{
     if(active.current!==recognition)return;
     const transcript=event.results[0]?.[0]?.transcript.trim();
     if(!transcript)return;
     received=true;
     onTranscript(transcript.slice(0,500));
     setStatus("Review the transcript before searching.");
   };
   recognition.onerror=event=>{
     received=true;
     setStatus(["not-allowed","service-not-allowed"].includes(event.error)
       ?"Microphone access was denied. Check your browser permissions or type your question."
       :"Voice input could not capture your question. Try again or type it.");
   };
   recognition.onend=()=>{
     active.current=null;
     setListening(false);
     if(!received)setStatus("No speech detected. Try again or type your question.");
   };
   try {
     recognition.start();
     setListening(true);
     setStatus("Listening…");
   } catch {
     active.current=null;
     setStatus("Voice input could not start. You can type your question.");
   }
 }
 return <div>
   <Button type="button" variant="outline" disabled={disabled} onClick={toggle}>
     {listening?<><Square size={16}/>Stop listening</>:<><Mic size={16}/>Speak your question</>}
   </Button>
   <p className="feature-muted">Your browser may send audio to its speech recognition service.</p>
   {status&&<p role="status">{status}</p>}
 </div>;
}
