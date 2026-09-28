'use client';
import {create} from 'zustand';
type Filters={team:string;week:string;setTeam:(team:string)=>void;setWeek:(week:string)=>void};
export const useFilters=create<Filters>(set=>({team:'ALL',week:'ALL',setTeam:team=>set({team}),setWeek:week=>set({week})}));
