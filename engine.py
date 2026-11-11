from fastapi import FastAPI
import networkx as nx
import random
import json
from fastapi.responses import FileResponse

app = FastAPI()

with open("devices.json", encoding="utf-8") as f:
    DEVICES = json.load(f)

PROTECTION_COST_USD = 40000
CRITICAL_PROTECTION_COST_USD = 60000

# الأنواع الحرجة تنفصل عن الأنواع العامة عند تفعيل الحماية
CRITICAL_TYPES = {"Cooling", "Payment"}


def build_graph(segmented=False, protected=False):
    g = nx.Graph()
    for d in DEVICES:
        g.add_node(d["id"], type=d["type"], value_usd=d["value_usd"])

    if not segmented:
        # شبكة مدمجة: كل الأجهزة على سويتش واحد (نجمة)
        for d in DEVICES:
            if d["id"] != "switch-1":
                g.add_edge("switch-1", d["id"])
    else:
        # بعد الفصل: سويتش للمنطقة العامة وسويتش للمنطقة الحرجة
        if not protected:
            g.add_node("switch-2", type="Switch", value_usd=10000)
        for d in DEVICES:
            if d["type"] == "Switch":
                continue
            if d["type"] in CRITICAL_TYPES:
                if protected:
                    # حماية الأجهزة الحرجة: كل جهاز معزول بذاته
                    continue
                hub = "switch-2"
            else:
                hub = "switch-1"
            g.add_edge(hub, d["id"])
    return g


def calc_loss(g, entry="kiosk-1"):
    # كل جهاز يكدر الهاكر يوصله (مباشر أو غير مباشر)
    reachable = nx.node_connected_component(g, entry) - {entry}
    return sum(g.nodes[n]["value_usd"] for n in reachable), sorted(reachable)


def worst_case(g):
    # أسوأ نقطة دخول ممكنة للهاكر بالشبكة
    rows = [(d["id"], calc_loss(g, d["id"])[0]) for d in DEVICES]
    entry, loss = max(rows, key=lambda r: r[1])
    return loss, entry


def simulate_attack(g, entry="kiosk-1", p_success=0.6, runs=10000):
    total_loss = 0
    for _ in range(runs):
        # الهاكر يبدأ من نقطة الدخول ويحاول يتوسع خطوة بخطوة
        owned = {entry}
        frontier = [entry]
        while frontier:
            current = frontier.pop()
            for nb in g.neighbors(current):
                if nb not in owned and random.random() < p_success:
                    owned.add(nb)
                    frontier.append(nb)
        total_loss += sum(g.nodes[n]["value_usd"] for n in owned - {entry})
    return round(total_loss / runs)


@app.get("/")
def home():
    return {"message": "Cyber-ROI Engine is running"}


@app.get("/network")
def network():
    return {"devices": DEVICES}


@app.get("/graph")
def graph():
    g = build_graph()
    return {
        "nodes": g.number_of_nodes(),
        "edges": g.number_of_edges(),
        "kiosk_can_reach": list(g.neighbors("kiosk-1")),
    }


@app.get("/risk")
def risk():
    g = build_graph()
    loss, reachable = calc_loss(g)
    return {
        "entry_point": "kiosk-1",
        "devices_exposed": len(reachable),
        "potential_loss_usd": loss,
    }


@app.get("/roi")
def roi(protection_cost: int = PROTECTION_COST_USD):
    loss_before, exposed_before = calc_loss(build_graph(segmented=False))
    loss_after, exposed_after = calc_loss(build_graph(segmented=True))
    saved = loss_before - loss_after
    return {
        "loss_before_usd": loss_before,
        "loss_after_usd": loss_after,
        "protection_cost_usd": protection_cost,
        "saved_usd": saved,
        "roi_percent": round((saved - protection_cost) / protection_cost * 100),
        "exposed_before": exposed_before,
        "exposed_after": exposed_after,
    }


@app.get("/simulate")
def simulate(p_success: float = 0.6, runs: int = 10000):
    before = simulate_attack(build_graph(segmented=False), p_success=p_success, runs=runs)
    after = simulate_attack(build_graph(segmented=True), p_success=p_success, runs=runs)
    return {
        "runs": runs,
        "p_success": p_success,
        "expected_loss_before_usd": before,
        "expected_loss_after_usd": after,
        "expected_saved_usd": before - after,
    }


@app.get("/bottlenecks")
def bottlenecks():
    def ranked(g):
        scores = nx.betweenness_centrality(g)
        return sorted(
            [{"id": n, "score": round(s, 3), "value_usd": g.nodes[n]["value_usd"]}
             for n, s in scores.items()],
            key=lambda x: x["score"],
            reverse=True,
        )

    return {
        "before_segmentation": ranked(build_graph(segmented=False)),
        "after_segmentation": ranked(build_graph(segmented=True)),
    }


@app.get("/priorities")
def priorities():
    def per_device(g):
        rows = []
        for d in DEVICES:
            loss, reachable = calc_loss(g, entry=d["id"])
            rows.append({
                "entry_point": d["id"],
                "type": d["type"],
                "devices_exposed": len(reachable),
                "loss_usd": loss,
            })
        return sorted(rows, key=lambda x: x["loss_usd"], reverse=True)

    return {
        "before_segmentation": per_device(build_graph(segmented=False)),
        "after_segmentation": per_device(build_graph(segmented=True)),
    }


@app.get("/scenarios")
def scenarios(
    segmentation_cost: int = PROTECTION_COST_USD,
    critical_protection_cost: int = CRITICAL_PROTECTION_COST_USD,
):
    plans = [
        ("no_protection", build_graph(), 0),
        ("segmentation", build_graph(segmented=True), segmentation_cost),
        (
            "segmentation_plus_critical",
            build_graph(segmented=True, protected=True),
            segmentation_cost + critical_protection_cost,
        ),
    ]
    base_loss, _ = worst_case(plans[0][1])
    result = []
    for name, g, cost in plans:
        loss, entry = worst_case(g)
        saved = base_loss - loss
        result.append({
            "scenario": name,
            "worst_case_loss_usd": loss,
            "worst_entry_point": entry,
            "cost_usd": cost,
            "saved_usd": saved,
            "roi_percent": round((saved - cost) / cost * 100) if cost else None,
        })
    return {"scenarios": result}
@app.get("/dashboard")
def dashboard():
    return FileResponse("dashboard.html")