import networkx as nx
from ai_hacker import choose_target


def test_choose_highest_value_target():
    graph = nx.Graph()

    graph.add_node("start", value_usd=0)
    graph.add_node("target_1", value_usd=1000)
    graph.add_node("target_2", value_usd=5000)

    graph.add_edges_from([
        ("start", "target_1"),
        ("start", "target_2")
    ])

    result = choose_target(graph, "start")

    assert result["target"] == "target_2"
    assert result["financial_impact"] == 5000


def test_exclude_owned_nodes():
    graph = nx.Graph()

    graph.add_node("start", value_usd=0)
    graph.add_node("owned", value_usd=10000)
    graph.add_node("target", value_usd=2000)

    graph.add_edges_from([
        ("start", "owned"),
        ("start", "target")
    ])

    result = choose_target(graph, "start", owned={"start", "owned"})

    assert result["target"] == "target"
    assert result["financial_impact"] == 2000


def test_no_available_targets():
    graph = nx.Graph()

    graph.add_node("start", value_usd=1000)

    result = choose_target(graph, "start")

    assert result is None


def test_multiple_owned_nodes():
    graph = nx.Graph()

    graph.add_node("start", value_usd=0)
    graph.add_node("second", value_usd=0)
    graph.add_node("target_1", value_usd=1000)
    graph.add_node("target_2", value_usd=3000)

    graph.add_edges_from([
        ("start", "target_1"),
        ("second", "target_2")
    ])

    result = choose_target(
        graph,
        "start",
        owned={"start", "second"}
    )

    assert result["target"] == "target_2"
    assert result["financial_impact"] == 3000