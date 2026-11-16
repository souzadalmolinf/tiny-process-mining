"""Discover and draw a directly-follows graph from the sample orders."""

from pathlib import Path

from graphviz import Digraph
import pm4py

from load_events import load_log


OUTPUT_DIR = Path(__file__).parent / "charts"


def main() -> None:
    log = load_log()
    flows, starts, ends = pm4py.discover_dfg(log)
    activity_counts = pm4py.get_event_attribute_values(log, "concept:name")

    graph = Digraph("orders")
    graph.attr(
        rankdir="TB",
        bgcolor="#0B1220",
        pad="0.45",
        nodesep="0.55",
        ranksep="0.75",
        splines="spline",
        label=f"ORDER TO DELIVERY  |  {log['case:concept:name'].nunique()} ORDERS · {len(log)} EVENTS",
        labelloc="t",
        fontname="Helvetica-Bold",
        fontsize="20",
        fontcolor="#E2E8F0",
    )
    graph.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontname="Helvetica",
        fontsize="12",
        margin="0.22,0.14",
        penwidth="0",
    )
    graph.attr("edge", fontname="Helvetica-Bold", fontsize="11", arrowsize="0.75")

    graph.node("START", "START", fillcolor="#0F766E", fontcolor="white")
    graph.node("END", "END", fillcolor="#0F766E", fontcolor="white")

    for activity, count in sorted(activity_counts.items()):
        if activity in {"Order cancelled", "Refunded"}:
            color = "#783653"
        elif activity in {"Delivery delayed", "Delivery attempted"}:
            color = "#92400E"
        elif activity == "Delivered":
            color = "#166534"
        else:
            color = "#1E3A5F"
        event_label = "event" if count == 1 else "events"
        graph.node(activity, f"{activity}\n{count} {event_label}", fillcolor=color, fontcolor="white")

    def add_edge(source: str, target: str, count: int) -> None:
        exception = target in {"Order cancelled", "Refunded", "Delivery delayed", "Delivery attempted"}
        color = "#F59E0B" if exception else "#38BDF8"
        graph.edge(
            source,
            target,
            label=str(count),
            color=color,
            fontcolor="#CBD5E1",
            penwidth=str(1.4 + count * 0.45),
        )

    for activity, count in sorted(starts.items()):
        add_edge("START", activity, count)
    for (source, target), count in sorted(flows.items()):
        add_edge(source, target, count)
    for activity, count in sorted(ends.items()):
        add_edge(activity, "END", count)

    OUTPUT_DIR.mkdir(exist_ok=True)
    for image_format in ("svg", "png"):
        (OUTPUT_DIR / f"process_graph.{image_format}").write_bytes(
            graph.pipe(format=image_format)
        )
    print(f"Saved process graph to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
