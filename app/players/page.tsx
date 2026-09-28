import players from '@/public/data/players_enriched.json';
import SiteNav from '@/app/components/SiteNav';
import PlayerSearch from './PlayerSearch';
export default function Players(){return <main><SiteNav/><div className="data-content"><div className="eyebrow">THE PEOPLE BEHIND THE PLAYS</div><h1>PLAYER<br/><span>VAULT.</span></h1><PlayerSearch players={players}/></div></main>}
