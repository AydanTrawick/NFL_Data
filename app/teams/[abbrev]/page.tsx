import stats from '@/public/data/team_stats.json';
import TeamCharts from '@/app/components/TeamCharts';
import teams from '@/public/data/teams_enriched.json';
import games from '@/public/data/games.json';
import SiteNav from '@/app/components/SiteNav';
import type {CSSProperties} from 'react';
import {notFound} from 'next/navigation';
function contrast(hex:string){const rgb=hex.replace('#','').match(/.{2}/g)?.map(x=>{const v=parseInt(x,16)/255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4})||[0,0,0];return (.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]+.05)/.053;}
export function generateStaticParams(){return teams.map(t=>({abbrev:t.abbrev}))}
export default async function Team({params}:{params:Promise<{abbrev:string}>}){const {abbrev}=await params,t=teams.find(t=>t.abbrev===abbrev);if(!t)notFound();const gs=games.filter(g=>[g.offense.toUpperCase(),g.defense.toUpperCase()].includes(abbrev)).sort((a,b)=>new Date(a.date).getTime()-new Date(b.date).getTime());const advanced=stats[abbrev as keyof typeof stats];const accent=[t.color,t.secondaryColor,'#c8f31d'].find(c=>contrast(c)>=4.5)!;return <main className="team-theme" style={{'--team-accent':accent,'--team-glow':t.color+'40'} as CSSProperties}><SiteNav/><div className="data-content" style={{borderTop:`4px solid ${t.color}`}}><div className="eyebrow">TEAM HUB · {t.name}</div><h1>{t.abbrev}<br/><span>ALL IN.</span></h1><div className="data-metrics"><div><b>{t.wins}–{t.losses}–{t.ties}</b><span>ALL GAMES</span></div><div><b>{t.games}</b><span>GAMES</span></div><div><b>{`${Math.round(advanced.passRate*100)}%`}</b><span>PASS SHARE</span></div><div><b>{t.runEvents}</b><span>RUN EVENTS</span></div></div><TeamCharts stats={stats[abbrev as keyof typeof stats]}/><h2>THE SEASON</h2><div className="result-list">{gs.map(g=><a key={g.id} href={`/games/${g.id}`}><span>{g.date}</span><b>{g.offense.toUpperCase()} {g.offenseScore} — {g.defenseScore} {g.defense.toUpperCase()}</b><small>{g.type} ↗</small></a>)}</div></div></main>}
