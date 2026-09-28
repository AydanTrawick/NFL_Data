import SeasonStory from '@/app/components/SeasonStory';
import games from "@/public/data/games.json";
import teams from "@/public/data/teams.json";
import metadata from "@/public/data/metadata.json";

const stats = [
  { value: metadata.offensivePlays.toLocaleString(), label: "OFFENSIVE PLAYS" },
  { value: String(games.length), label: "GAMES IN THE FILE" },
  { value: String(teams.length), label: "TEAMS" },
  { value: `${metadata.superBowl?.defenseScore}—${metadata.superBowl?.offenseScore}`, label: `SUPER BOWL · ${metadata.superBowl?.defense?.toUpperCase()}—${metadata.superBowl?.offense}` },
];

export default function Home() {
  return <main>
    <nav className="nav"><a className="brand" href="#top"><span className="brand-mark">E</span> EVERY SNAP</a><div className="nav-right"><a href="/teams">TEAMS</a><a href={`/games/${metadata.superBowl?.id}`}>GAME FLOW</a><a href="/players">PLAYERS</a><a href="/bracket">PLAYOFFS</a><a href="/play">CALL THE PLAY</a><a href="/map">SEASON MAP</a><a href="/about-the-data">DATA NOTES ↗</a></div></nav>
    <section className="hero" id="top">
      <div className="hero-grid" aria-hidden="true" />
      <div className="hero-copy"><div className="eyebrow"><span className="live-dot" /> THE 2025 NFL SEASON · A PLAY-BY-PLAY ATLAS</div>
        <h1>EVERY<br/><span>SNAP.</span></h1>
        <p className="dek">One season. {games.length} games. Every moment that moved the chains, changed the score, or changed everything.</p>
        <a className="cta" href="#chapters"><span>ENTER THE SEASON</span><b>↓</b></a>
      </div>
      <div className="orbit" aria-hidden="true"><div className="orbit-ring ring-one"/><div className="orbit-ring ring-two"/><div className="orbit-ring ring-three"/><div className="orbit-ball"><span /></div><div className="orbit-label">2025—26<br/>SEASON ARCHIVE</div></div>
      <div className="hero-index">01 <i/> 07</div>
      <div className="hero-side">FROM KICKOFF TO THE FINAL WHISTLE</div>
    </section>
    <section className="ticker" aria-label="Season totals"><div className="ticker-track">{[...stats,...stats].map((s,i)=><div className="ticker-item" key={i}><strong>{s.value}</strong><span>{s.label}</span></div>)}</div></section>
    <SeasonStory/><section id="season" className="finale">
      <div className="section-kicker"><span>THE FINAL FRAME</span><span>{metadata.superBowl?.date} · {metadata.superBowl?.type.toUpperCase()}</span></div>
      <div className="final-card"><div className="final-watermark">LX</div><div className="final-copy"><div className="final-label">THE SEASON ENDS HERE</div><h2>ONE LAST<br/>SCOREBOARD.</h2><p>From the opening kickoff to the final snap in Santa Clara.</p><a href="/about-the-data" className="text-link">EXPLORE THE DATA <span>↗</span></a></div>
        <div className="scoreboard"><div className="score-head"><span>SUPER BOWL · FINAL</span><span>{metadata.superBowl?.date}</span></div><div className="score-row"><span className="team-glyph pats">{metadata.superBowl?.offense}</span><span className="team-name">{metadata.superBowl?.offense}</span><strong>{metadata.superBowl?.offenseScore}</strong></div><div className="score-row winner"><span className="team-glyph hawks">{metadata.superBowl?.defense?.toUpperCase()}</span><span className="team-name">{metadata.superBowl?.defense?.toUpperCase()}</span><strong>{metadata.superBowl?.defenseScore}</strong></div><div className="score-foot"><span>{metadata.superBowl?.type}</span><span>FINAL SCORE · SOURCE DATA</span></div></div></div>
    </section>
    <footer><span>EVERY SNAP <b>·</b> 2025 NFL SEASON</span><a href="/about-the-data">ABOUT THE DATA</a><span>BUILT FROM {metadata.eventRows.toLocaleString()} SOURCE EVENTS</span><a href="/ask">FILM ROOM</a></footer>
  </main>;
}
