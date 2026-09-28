import venues from '@/public/data/game_venues.json';
import games from '@/public/data/games.json';
import drives from '@/public/data/drives.json';
import teams from '@/public/data/teams_enriched.json';
import SiteNav from '@/app/components/SiteNav';
import GameExperience from './DriveReplayLoader';
import {notFound} from 'next/navigation';
export function generateStaticParams(){return games.map(g=>({id:g.id}))}
export default async function Game({params}:{params:Promise<{id:string}>}){const {id}=await params,g=games.find(g=>g.id===id);if(!g)notFound();const a=g.offense.toUpperCase(),b=g.defense.toUpperCase();const venue=venues[id as keyof typeof venues];return <main><SiteNav/><div className="data-content game-content"><div className="eyebrow">{g.type.toUpperCase()} · {g.date}</div><h1>{a} <span>vs {b}</span></h1><p className="game-final">FINAL <b>{g.offenseScore} — {g.defenseScore}</b></p><div className="weather-badge">{venue?.stadium||'Venue unavailable'} · {venue?.isDome?'CLOSED ROOF':venue?.weather?`${venue.weather.temperatureF}°F · WIND ${venue.weather.windMph} MPH · ${venue.weather.precipitationMm} MM`:"Weather unavailable"}{venue?.weather&&<small>Hourly outdoor estimate · Open-Meteo{venue.roof==='unknown'?' · roof status unverified':''}</small>}</div><GameExperience gameId={id} teamA={a} teamB={b} colors={[teams.find(t=>t.abbrev===a)?.color||'#315f45',teams.find(t=>t.abbrev===b)?.color||'#41516a']} drives={drives.filter(d=>d.gameId===id).sort((a,b)=>a.order-b.order)}/></div></main>}
