from app.graph import build_graph

# For local testing or import
graph = build_graph()

if __name__ == "__main__":
    # Simple CLI test
    print("Graph compiled.")
    try:
        graph.get_graph().draw_mermaid_png(output_file_path="graph.png")
        print("Graph visualization saved to graph.png")
    except Exception as e:
        print(f"Could not draw graph: {e}")
