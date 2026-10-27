"""Environmental wear and route-use summaries; no claim of causal benefit."""
import math

def summarize_counts(counts,start=None,static_tile_costs=False):
    counts=[float(n) for n in counts]
    if not counts or any(not math.isfinite(n) or n<0 for n in counts):
        raise ValueError('Invalid traversal counts')
    total=sum(counts);visited=[n for n in counts if n>0]
    entropy=-sum((n/total)*math.log(n/total) for n in visited) if total else 0.
    result=dict(tile_count=len(counts),total_tile_counts=total,visited_tiles=len(visited),
        revisited_tiles=sum(n>=2 for n in counts),maximum_tile_count=max(counts),
        fraction_entries_revisiting=(total-len(visited))/total if total else 0.,
        mean_visited_next_cost_fraction_of_first=(1. if static_tile_costs else sum(2/(n+2) for n in visited)/len(visited)) if visited else None,
        cumulative_visit_entropy=entropy,effective_visited_tiles=math.exp(entropy) if total else 0.)
    if start is not None:
        if len(start)!=len(counts):raise ValueError('Mismatched tile histories')
        if any(not math.isfinite(n) or n<0 for n in start):raise ValueError('Invalid initial counts')
        delta=[n-p for n,p in zip(counts,start)]
        if any(n<0 for n in delta):raise ValueError('Count reset or retention change inside measurement window')
        entries=sum(delta);new=sum(p==0 and n>0 for p,n in zip(start,delta))
        positive=[n for n in delta if n>0]
        window_entropy=-sum((n/entries)*math.log(n/entries) for n in positive) if entries else 0.
        result.update(window_entries=entries,window_distinct_tiles=len(positive),window_first_visits=new,
            window_fraction_entries_revisiting=(entries-new)/entries if entries else 0.,
            window_visit_entropy=window_entropy,window_effective_visited_tiles=math.exp(window_entropy) if entries else 0.)
    return result
