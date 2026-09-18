from agents.supervisor.graph import supervisor_graph
from agents.research.graph import research_graph
from agents.planning.graph import planning_graph
from agents.review.graph import review_graph


graphs = {
    "supervisor_graph.png": supervisor_graph,
    "research_graph.png": research_graph,
    "planning_graph.png": planning_graph,
    "review_graph.png": review_graph,
}


def main():
    for filename, graph in graphs.items():
        png_data = graph.get_graph().draw_mermaid_png()

        with open(filename, "wb") as f:
            f.write(png_data)

        print(f"saved: {filename}")


if __name__ == "__main__":
    main()