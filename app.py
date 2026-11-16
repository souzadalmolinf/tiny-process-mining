"""Interactive process map for the synthetic order event log."""

import pm4py
import streamlit as st

from load_events import load_log


POSITIONS = {
    "Order placed": (80, 260),
    "Payment confirmed": (270, 260),
    "Packed": (460, 260),
    "Shipped": (650, 260),
    "Out for delivery": (850, 260),
    "Delivered": (1060, 260),
    "Order cancelled": (330, 75),
    "Refunded": (560, 75),
    "Delivery delayed": (730, 450),
    "Delivery attempted": (970, 450),
}

SHORT_LABELS = {
    "Payment confirmed": "Payment\nconfirmed",
    "Out for delivery": "Out for\ndelivery",
    "Order cancelled": "Order\ncancelled",
    "Delivery delayed": "Delivery\ndelayed",
    "Delivery attempted": "Delivery\nattempted",
}


def activity_color(activity: str) -> str:
    if activity in {"Order cancelled", "Refunded"}:
        return "#9D4EDD"
    if activity in {"Delivery delayed", "Delivery attempted"}:
        return "#F59E0B"
    if activity == "Delivered":
        return "#10B981"
    return "#2563EB"


def graph_spec(all_log, selected_log, show_all: bool) -> dict:
    all_flows, _, _ = pm4py.discover_dfg(all_log)
    selected_flows, _, _ = pm4py.discover_dfg(selected_log)
    counts = pm4py.get_event_attribute_values(selected_log, "concept:name")

    nodes = []
    for activity, (x, y) in POSITIONS.items():
        count = counts.get(activity, 0)
        active = show_all or count > 0
        nodes.append(
            {
                "name": activity,
                "value": count,
                "x": x,
                "y": y,
                "symbol": "roundRect",
                "symbolSize": [108, 68],
                "itemStyle": {
                    "color": "#192B42" if active else "#202B3B",
                    "borderColor": activity_color(activity) if active else "#42536A",
                    "borderWidth": 2,
                    "shadowBlur": 10 if active else 0,
                    "shadowColor": "rgba(0, 0, 0, 0.2)",
                },
                "label": {
                    "show": True,
                    "position": "inside",
                    "formatter": (
                        f"{SHORT_LABELS.get(activity, activity)}\n{count} event{'s' if count != 1 else ''}"
                        if active
                        else SHORT_LABELS.get(activity, activity)
                    ),
                    "color": "#FFFFFF" if active else "#8FA2B9",
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "lineHeight": 16,
                },
            }
        )

    links = []
    for source, target in all_flows:
        count = selected_flows.get((source, target), 0)
        active = show_all or count > 0
        exceptional = source in {
            "Order cancelled", "Refunded", "Delivery delayed", "Delivery attempted"
        } or target in {
            "Order cancelled", "Refunded", "Delivery delayed", "Delivery attempted"
        }
        links.append(
            {
                "source": source,
                "target": target,
                "name": f"{source} → {target}",
                "value": count,
                "lineStyle": {
                    "color": ("#FBBF24" if exceptional else "#67E8F9") if active else "#607189",
                    "opacity": 0.88 if active else 0.12,
                    "width": 1.5 + count * 0.65 if active else 1,
                    "curveness": 0.32 if {source, target} == {
                        "Out for delivery", "Delivery attempted"
                    } else 0.08,
                },
            }
        )

    return {
        "backgroundColor": "transparent",
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}<br/>{c} occurrences",
            "backgroundColor": "#162338",
            "borderColor": "#344861",
            "textStyle": {"color": "#F1F5F9"},
        },
        "animationDurationUpdate": 300,
        "series": [
            {
                "type": "graph",
                "layout": "none",
                "left": 85,
                "right": 85,
                "top": 75,
                "bottom": 75,
                "data": nodes,
                "links": links,
                "roam": True,
                "draggable": False,
                "edgeSymbol": ["none", "arrow"],
                "edgeSymbolSize": [0, 10],
                "emphasis": {"focus": "adjacency"},
            }
        ],
    }


st.set_page_config(page_title="Order flow | Process mining", layout="wide")

log = load_log()
orders = sorted(log["case:concept:name"].unique())

st.caption("SYNTHETIC DATA  ·  PM4PY PROCESS DISCOVERY")
st.title("From order to doorstep")
st.write("Explore how five example purchases moved through payment, shipping, delivery, and exceptions.")

selected_order = st.selectbox("Order", ["All orders", *orders])
show_all = selected_order == "All orders"
view = log if show_all else log[log["case:concept:name"] == selected_order]

orders_metric, events_metric, activities_metric = st.columns(3)
orders_metric.metric("Orders", view["case:concept:name"].nunique())
events_metric.metric("Events", len(view))
activities_metric.metric("Activities", view["concept:name"].nunique())

st.subheader("Process map")
st.caption("Each arrow shows a directly following activity. Thicker arrows occurred more often; amber marks exception paths. Drag to pan, scroll to zoom, or hover for counts.")
st.echarts_chart(
    graph_spec(log, view, show_all),
    height=590,
    theme=None,
    alt="Interactive order process map showing activity counts and directly following transitions",
)

if not show_all:
    st.subheader(f"Timeline · {selected_order}")
    timeline = view[["concept:name", "time:timestamp"]].rename(
        columns={"concept:name": "Activity", "time:timestamp": "Time (UTC)"}
    )
    timeline["Time (UTC)"] = timeline["Time (UTC)"].dt.strftime("%d %b %Y, %H:%M")
    st.dataframe(timeline, hide_index=True, width="stretch")
