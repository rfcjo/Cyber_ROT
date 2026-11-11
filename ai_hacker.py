import networkx as nx


def choose_target(graph: nx.Graph, current_node, owned=None):

    if owned is None:
        owned = {current_node}
    else:
        owned = set(owned)

    frontier = {
        neighbor
        for node in owned
        for neighbor in graph.neighbors(node)
        if neighbor not in owned
    }

    if not frontier:
        return None

    best_target = max(
        frontier,
        key=lambda node: graph.nodes[node]["value_usd"]
    )

    return {
        "target": best_target,
        "financial_impact": graph.nodes[best_target]["value_usd"]
    }


# =================================
# CYBER_ROT - SIMULATION ENGINE
# =================================

def run_simulation():

    graph = nx.Graph()

    graph.add_node("kiosk-1", value_usd=5000)
    graph.add_node("cctv-1", value_usd=20000)
    graph.add_node("bms-1", value_usd=150000)
    graph.add_node("pos-1", value_usd=300000)

    graph.add_edges_from([
        ("kiosk-1", "cctv-1"),
        ("kiosk-1", "bms-1"),
        ("kiosk-1", "pos-1")
    ])

    owned = {"kiosk-1"}
    total_impact = 0

    print("\n================================")
    print("       CYBER_ROT ENGINE")
    print("================================")

    print("\n[+] Virtual network initialized")
    print("[+] Entry node: kiosk-1")
    print("[+] Simulation started\n")

    for step in range(1, 4):

        result = choose_target(
            graph,
            "kiosk-1",
            owned
        )

        if result is None:
            print("[-] No eligible nodes remaining")
            break

        target = result["target"]
        impact = result["financial_impact"]

        print(f"[STEP {step}]")
        print(f"Selected node: {target}")
        print(f"Estimated financial impact: ${impact:,}")

        owned.add(target)
        total_impact += impact

        print("--------------------------------")

    print("\n[+] SIMULATION COMPLETED")
    print(f"[+] Selected nodes: {len(owned) - 1}")
    print(f"[+] Total simulated impact: ${total_impact:,}")

    print("\n================================")


if __name__ == "__main__":
    run_simulation()