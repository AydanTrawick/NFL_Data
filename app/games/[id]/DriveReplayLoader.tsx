"use client";
import dynamic from "next/dynamic";
type Event={driveId:string;team:string;quarter:number|null;clock:number|null;down:number;yardsToGo:number;yardLine:number|null;yardsGained:number|null;offenseScore:number|null;defenseScore:number|null;scoring:boolean;scoringPlayer:string;call:string;result:string};
const DriveReplayer=dynamic(()=>import("./DriveReplayer3D"),{ssr:false,loading:()=> <div className="replay-loading">LOADING 3D FIELD…</div>});
export default function DriveReplayLoader({events,offense,defense,offColor,defColor}:{events:Event[];offense:string;defense:string;offColor:string;defColor:string}){return <DriveReplayer events={events} offense={offense} defense={defense} offColor={offColor} defColor={defColor}/>}
