import {useLayoutEffect, useMemo, useRef, useState, type ReactNode} from "react";
import {ArrowRight, Check, ChevronDown, Clock, MapPin, RotateCcw, Search} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Empty, EmptyHeader, EmptyTitle, EmptyDescription} from "@/components/ui/empty";
import type {Resource} from "@/lib/types";

const BATCH = 9;
// Give the first page a mix of campus needs. Only actual, published matches are passed in.
const STARTING_OFFICES = new Map([
  "financial-aid", "registrar", "it-service-desk", "mav-card", "central-library",
  "career-center", "health-services", "student-access", "parking",
].map((id, index) => [id, index]));

type Props = {
  resources: Resource[];
  headline: string;
  searching:boolean;
  fallback:boolean;
  home: boolean;
  busy: boolean;
  onRefresh: () => void;
  onClear: () => void;
  onAsk?: () => void;
  onOpen: (id: string) => void;
  icon: (resource: Resource) => ReactNode;
  bookmark: (resource: Resource) => ReactNode;
};

export function DirectoryResults({resources, headline, searching, fallback, home, busy, onRefresh, onClear, onAsk, onOpen, icon, bookmark}: Props) {
  const [limit, setLimit] = useState(BATCH);
  const grid = useRef<HTMLDivElement>(null);
  const firstNew = useRef<number | null>(null);
  const ordered = useMemo(() => home
    ? [...resources].sort((a, b) => (STARTING_OFFICES.get(a.id) ?? BATCH) - (STARTING_OFFICES.get(b.id) ?? BATCH))
    : resources, [resources, home]);
  const total = ordered.length;
  const shown = Math.min(limit, total);
  const more = shown < total;

  function loadMore() {
    if (!more) return;
    firstNew.current = shown;
    setLimit(shown + BATCH);
  }
  // After appending, continue from the first new card, including when the last batch removes the button.
  useLayoutEffect(() => {
    if (firstNew.current === null) return;
    const title = grid.current?.querySelectorAll<HTMLButtonElement>("h3 button")[firstNew.current];
    firstNew.current = null;
    if (!title) return;
    title.focus({preventScroll: true});
    title.closest("article")?.scrollIntoView({block: "nearest", inline: "nearest"});
  }, [limit]);

  return <>
    <div className="results-toolbar directory-toolbar">
      <div>
        <h2 id="directory-results-heading">{headline}</h2>
        <p className="results-count" role="status" aria-live="polite" aria-atomic="true">
          {searching ? "Searching campus services…" : total === 0 ? "0 matching resources" : `Showing ${shown} of ${total} ${total === 1 ? "resource" : "resources"}`}
        </p>
      </div>
      <Button variant="ghost" size="icon" disabled={busy} aria-label="Refresh directory" title="Refresh directory" onClick={onRefresh}>
        <RotateCcw size={17} className={busy ? "animate-spin" : ""}/>
      </Button>
    </div>
    {fallback&&<p className="directory-searching" role="status">Showing keyword matches from this directory. Refresh to retry the service search.</p>}
    {searching&&total===0?<div className="directory-searching">Looking for offices that can help…</div>:total === 0 ? <Empty className="empty-state">
      <Search size={34} aria-hidden="true"/>
      <EmptyHeader><EmptyTitle>No resources found</EmptyTitle><EmptyDescription>{onAsk?"Try a shorter keyword or take this question to the resource guide.":"Try a different keyword or choose another category."}</EmptyDescription></EmptyHeader>
      <div className="empty-actions">{onAsk&&<Button onClick={onAsk}>Ask the guide <ArrowRight size={16}/></Button>}<Button variant="outline" onClick={onClear}>Clear filters</Button></div>
    </Empty> : <>
      <div id="directory-resource-grid" className="resource-grid" aria-labelledby="directory-results-heading" ref={grid}>
        {ordered.slice(0, shown).map(r => <article className="resource-card" key={r.id}>
          <div className="card-top">
            <span className="resource-icon" style={{color:r.category_color, background:r.category_color+"10"}}>{icon(r)}</span>
            <span className="category-label">{r.category_name}</span><span className="card-save">{bookmark(r)}</span>
          </div>
          <h3><button className="resource-name" onClick={() => onOpen(r.id)}>{r.name}</button></h3>
          <p className="resource-summary">{r.summary}</p>
          <div className="resource-meta">
            <span title={r.location}><MapPin size={15} aria-hidden="true"/><span><span className="sr-only">Location: </span>{r.location}</span></span><span title={r.hours}><Clock size={15} aria-hidden="true"/><span><span className="sr-only">Hours: </span>{r.hours}</span></span>
          </div>
          <div className="card-bottom">
            <button className="details-button" aria-label={`Office details: ${r.name}`} onClick={() => onOpen(r.id)}>Office details <ArrowRight size={16}/></button>
          </div>
        </article>)}
      </div>
      {total > BATCH && <div className="directory-pager">
        {more ? <>
          <Button className="load-more-resources" variant="outline" type="button"
            aria-controls="directory-resource-grid" aria-describedby="remaining-resources" onClick={loadMore}>
            Load more <ChevronDown size={17} aria-hidden="true"/>
          </Button>
          <span id="remaining-resources" className="pager-note">{shown} of {total} shown · {total - shown} remaining</span>
        </> : <span className="pager-note pager-complete"><Check size={15} aria-hidden="true"/> All {total} resources shown</span>}
      </div>}
    </>}
  </>;
}
