"use client";
import {Canvas,useFrame} from "@react-three/fiber";
import {useEffect,useMemo,useRef,useState} from "react";
import type {Mesh} from "three";

type Event={driveId:string;team:string;quarter:number|null;clock:number|null;down:number;yardsToGo:number;yardLine:number|null;yardsGained:number|null;offenseScore:number|null;defenseScore:number|null;scoring:boolean;scoringPlayer:string;call:string;result:string};
function Field({ballX,ballY,overhead,offColor,defColor}:{ballX:number;ballY:number;overhead:boolean;offColor:string;defColor:string}){
  const ball=useRef<Mesh>(null);useFrame((_state,delta)=>{if(ball.current){const step=Math.min(1,delta*7);ball.current.position.x+=(ballX-ball.current.position.x)*step;ball.current.position.y+=(ballY-ball.current.position.y)*step;ball.current.rotation.z+=delta*.8;ball.current.rotation.x+=delta*.2}});
  return <>
    <ambientLight intensity={1.7}/><directionalLight position={[0,28,15]} intensity={2.2}/>
    <mesh rotation={[-Math.PI/2,0,0]} position={[0,0,0]}><planeGeometry args={[112,53]}/><meshStandardMaterial color="#163b2a" roughness={.95}/></mesh>
    <mesh position={[-54,0.08,0]}><boxGeometry args={[8,.15,53]}/><meshStandardMaterial color={defColor}/></mesh>
    <mesh position={[54,0.08,0]}><boxGeometry args={[8,.15,53]}/><meshStandardMaterial color={offColor}/></mesh>
    {Array.from({length:21},(_,i)=><mesh key={i} position={[-50+i*5,0.1,0]}><boxGeometry args={[i%2===0?.16:.08,.08,49]}/><meshStandardMaterial color="#d7e6d2" transparent opacity={.38}/></mesh>)}
    {[-17,-11,-5,5,11,17].map(z=><mesh key={z} position={[0,.11,z]}><boxGeometry args={[100,.07,.08]}/><meshStandardMaterial color="#d7e6d2" transparent opacity={.45}/></mesh>)}
    <mesh ref={ball} position={[ballX,ballY,0]} scale={[1.1,.38,.44]}><sphereGeometry args={[1,24,16]}/><meshStandardMaterial color="#a85827" roughness={.33} metalness={.1}/></mesh>
    <mesh position={[ballX,ballY+.43,0]}><boxGeometry args={[.62,.055,.055]}/><meshStandardMaterial color="#f3eee0"/></mesh>
  </>
}
function yardX(yardLine:number|null){return Math.max(-48,Math.min(48,50-(yardLine??50)))}
export default function DriveReplayer3D({events,offense,defense,offColor,defColor}:{events:Event[];offense:string;defense:string;offColor:string;defColor:string}){
  const [index,setIndex]=useState(0),[playing,setPlaying]=useState(false),[speed,setSpeed]=useState(1),[camera,setCamera]=useState<"BROADCAST"|"ALL-22">("BROADCAST"),[small,setSmall]=useState(false);
  useEffect(()=>{const m=window.matchMedia("(max-width: 600px)");const update=()=>setSmall(m.matches);update();m.addEventListener("change",update);return()=>m.removeEventListener("change",update)},[]);
  const usable=useMemo(()=>events.slice().sort((a,b)=>Number(a.driveId)-Number(b.driveId)||(a.quarter??0)-(b.quarter??0)||(b.clock??0)-(a.clock??0)),[events]);
  useEffect(()=>{if(!playing||usable.length<2)return;const timer=window.setInterval(()=>setIndex(i=>{if(i>=usable.length-1){setPlaying(false);return i}return i+1}),1050/speed);return()=>window.clearInterval(timer)},[playing,speed,usable.length]);
  if(!usable.length)return <div className="replay-loading">NO SCRIMMAGE EVENTS AVAILABLE FOR A REPLAY EXCERPT.</div>;
  const event=usable[Math.min(index,usable.length-1)],x=yardX(event.yardLine),isPass=event.call==="Pass",arc=isPass?3.7:1.05;
  return <section className="replay-panel" aria-label="Drive replayer">
    <div className="replay-title"><div><span className="eyebrow">SAMPLED GAME EXCERPT · {usable.length} EVENTS</span><h2>DRIVE <b>{event.driveId||"—"}</b></h2></div><div className="replay-team-label"><span style={{background:offColor}}/>{offense}<i/> {defense}<span style={{background:defColor}}/></div></div>
    <div className="replay-scene">
      {small?<div className="field-2d" role="img" aria-label={`${event.team} ball at ${event.yardLine??"unknown"} yards from target end zone`}><div className="end-zone left" style={{background:defColor}}/><div className="end-zone right" style={{background:offColor}}/><div className="field-midline"/><div className="ball-marker" style={{left:`${Math.max(5,Math.min(95,x+50))}%`}}/><span className="field-label left-label">{defense}</span><span className="field-label right-label">{offense}</span></div>
        :<Canvas dpr={[1,1.5]} camera={camera==="ALL-22"?{position:[0,86,.1],fov:42}:{position:[0,43,67],fov:46}} fallback={<div className="replay-loading">WebGL unavailable. Use the mobile field view.</div>}><Field ballX={x} ballY={arc} overhead={camera==="ALL-22"} offColor={offColor} defColor={defColor}/></Canvas>}
      {event.scoring&&<div className="moment-banner"><span>SCORING MOMENT</span><b>{event.scoringPlayer||event.result}</b></div>}
      <div className="score-bug"><strong>{event.team}</strong><span>Q{event.quarter??"—"} · {event.clock==null?"—:—":`${Math.floor(event.clock/60)}:${String(event.clock%60).padStart(2,"0")}`}</span><b>{event.offenseScore??"—"} — {event.defenseScore??"—"}</b><small>{event.down}{event.down===1?"ST":event.down===2?"ND":event.down===3?"RD":"TH"} &amp; {event.yardsToGo}</small></div>
    </div>
    <div className="replay-controls"><button onClick={()=>setPlaying(v=>!v)}>{playing?"PAUSE":"PLAY"}</button><select aria-label="Playback speed" value={speed} onChange={e=>setSpeed(Number(e.target.value))}><option value={1}>1×</option><option value={2}>2×</option><option value={4}>4×</option></select><button className="view-toggle" onClick={()=>setCamera(v=>v==="ALL-22"?"BROADCAST":"ALL-22")}>{camera==="ALL-22"?"BROADCAST":"ALL-22"}</button><input aria-label="Replay timeline" type="range" min={0} max={usable.length-1} value={index} onChange={e=>{setPlaying(false);setIndex(Number(e.target.value))}}/><span>{index+1}/{usable.length}</span></div>
    <div className="replay-event"><b>{event.team}</b><span>{event.call} · {event.result} · {event.yardsGained==null?"gain unavailable":`${event.yardsGained} yards`}</span><span>{event.yardLine==null?"position unavailable":`${event.yardLine} yards from target end zone`}</span></div>
  </section>
}
