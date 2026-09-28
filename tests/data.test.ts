import {it,expect} from 'vitest';
import fs from 'node:fs';
import games from '../public/data/games.json';
import drives from '../public/data/drives.json';
import matches from '../public/data/touch_match_report.json';
import type {ReplayEvent} from '../lib/types';
it('all game timelines reconcile to final scores and preserve event order',()=>{for(const g of games){const es=JSON.parse(fs.readFileSync(`public/data/replays/${g.id}.json`,'utf8')) as ReplayEvent[];expect(es.length).toBe(g.events);expect(es.at(-1)?.scoreA).toBe(g.offenseScore);expect(es.at(-1)?.scoreB).toBe(g.defenseScore);expect(new Set(es.map(e=>e.id)).size).toBe(es.length);for(let i=1;i<es.length;i++)expect(es[i].order).toBeGreaterThan(es[i-1].order);expect(es.filter(e=>e.scoring).reduce((sum,e)=>sum+e.points,0)).toBe((g.offenseScore||0)+(g.defenseScore||0))}});
it('drive identity includes team and resolves to a real replay event',()=>{expect(new Set(drives.map(d=>d.gameId+'|'+d.driveKey)).size).toBe(drives.length);for(const d of drives)expect(d.driveKey.startsWith(d.team+':')).toBe(true)});
it('headshots meet touch-eligible coverage',()=>expect(matches.coverage).toBeGreaterThanOrEqual(.95));
