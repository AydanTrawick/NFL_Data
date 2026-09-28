import examples from '@/public/data/play_situations.json';
import situations from '@/public/data/situations.json';
import SiteNav from '@/app/components/SiteNav';
import PlayGame from './PlayGame';
export default function Play(){return <main><SiteNav/><div className="data-content"><div className="eyebrow">YOU'RE THE COORDINATOR</div><h1>CALL<br/><span>THE PLAY.</span></h1><p className="dek">Read the situation. Trust your instincts. Find out what really happened.</p><PlayGame examples={examples} situations={situations}/></div></main>}
