import argparse
import math
import re
from time import sleep, time
from dotenv import load_dotenv
import os
from multiprocessing import JoinableQueue, parent_process
import networkx
import multiprocessing
import json
from pyvis.network import Network
import signal


from onshape_api import OnshapeAPI


def parse_assembly_links(assembly_defintion: dict) -> list[dict]:
    connections = []
    for instance in assembly_defintion["rootAssembly"]["instances"]:
        if "isStandardContent" in instance.keys():
            if instance["isStandardContent"]:
                continue

        if "type" not in instance.keys():
            continue
        inst = {
            "type": instance["type"],
            "document_id": instance["documentId"],
            "element_id": instance["elementId"],
            "document_microversion": instance["documentMicroversion"],
        }
        if "documentVersion" in instance.keys():
            inst["document_version"] = instance["documentVersion"]
        connections.append(inst)
    return connections


def parse_partstudio_links(feature_list: dict, original_document_id: str) -> list[dict]:
    name_space_regex = r"d(?P<document_id>.+):\s*:v(?P<version_id>.+):\s*:e(?P<element_id>.+):\s*:m(?P<microversion>.+)"
    internal_name_space_regex = r"e(?P<element_id>.+):\s*:m(?P<microversion>.+)"

    def filter_function(feature: dict) -> bool:
        return feature["featureType"] == "importDerived"

    if "features" not in feature_list.keys():
        print("Something weird has happened")
        print(feature_list)
        return []

    filtered = list(filter(filter_function, feature_list["features"]))
    results = []
    for feature in filtered:
        for param in feature["parameters"]:
            if param["parameterId"] == "partStudio":
                if (
                    match := re.search(name_space_regex, param["namespace"])
                ) is not None:
                    link = {
                        "type": "Part",
                        "document_id": match.group("document_id"),
                        "document_version": match.group("version_id"),
                        "element_id": match.group("element_id"),
                    }
                    results.append(link)
                    break
                elif (
                    match := re.search(internal_name_space_regex, param["namespace"])
                ) is not None:
                    link = {
                        "type": "Part",
                        "document_id": original_document_id,
                        "document_microversion": match.group("microversion"),
                        "element_id": match.group("element_id"),
                    }
                else:
                    print(f"Could not match name space in: {param}")

    return results


def process(
    id: int,
    waiting,
    to_visit,
    visited,
    nodes,
    edges,
    graph_lock,
    visited_lock,
    waiting_lock,
):
    api = OnshapeAPI(os.environ.get("ACCESS_KEY"), os.environ.get("PRIVATE_KEY"))

    while True:
        visiting = to_visit.get()

        document_id = visiting["document_id"]
        element_id = visiting["element_id"]
        wvm = None
        wvm_id = ""
        if "workspace_id" in visiting.keys():
            wvm = "w"
            wvm_id = visiting["workspace_id"]
        elif "document_version" in visiting.keys():
            wvm = "v"
            wvm_id = visiting["document_version"]
        elif "document_microversion" in visiting.keys():
            wvm = "m"
            wvm_id = visiting["document_microversion"]
        if wvm is None:
            print(
                f"Something has gone wrong | 'w' : {'workspace_id' in visiting.keys()} | 'v' : {'document_version' in visiting.keys()} | 'm' : {'document_microversion' in visiting.keys()}"
            )
            print(visiting)
            return

        links = {}
        match visiting["type"]:
            case "Part":
                response = api.part_studio.get_features(
                    document_id, wvm, wvm_id, element_id, include_geometric_data=False
                )
                response = json.loads(response.text)
                links = parse_partstudio_links(response, document_id)
            case "Assembly":
                response = api.assembly.get_definition(
                    document_id, wvm, wvm_id, element_id
                )
                response = json.loads(response.text)
                links = parse_assembly_links(response)

        element = json.loads(
            api.document.get_elements(
                document_id, wvm, wvm_id, element_id=element_id
            ).text
        )[0]
        document = json.loads(api.document.get_document(document_id).text)

        node_name = f"{document['name']}|{element['name']}"

        print(f"Process {id} visited: {node_name}")

        for link in links:
            visited_lock.acquire()
            wvm = None
            wvm_id = ""
            if "workspace_id" in link.keys():
                wvm = "w"
                wvm_id = link["workspace_id"]
            elif "document_version" in link.keys():
                wvm = "v"
                wvm_id = link["document_version"]
            elif "document_microversion" in link.keys():
                wvm = "m"
                wvm_id = link["document_microversion"]
            if wvm is None:
                print(
                    f"Something has gone wrong | 'w' : {'workspace_id' in visiting.keys()} | 'v' : {'document_version' in visiting.keys()} | 'm' : {'document_microversion' in link.keys()}"
                )
                print(link)
                continue
            link_element = json.loads(
                api.document.get_elements(
                    link["document_id"], wvm, wvm_id, element_id=link["element_id"]
                ).text
            )[0]
            link_document = json.loads(
                api.document.get_document(link["document_id"]).text
            )
            link_node_name = f"{link_document['name']}|{link_element['name']}"
            if (link_id := (link["document_id"], link["element_id"])) not in visited:
                visited.add(link_id)
                visited_lock.release()

                to_visit.put(link)

                graph_lock.acquire()
                if link_node_name not in nodes:
                    nodes.append(link_node_name)
                graph_lock.release()

            else:
                visited_lock.release()
            graph_lock.acquire()
            edges.append((node_name, link_node_name))
            graph_lock.release()
        to_visit.task_done()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Onshape Graph Visualizer",
        description="Creates a visualization of the connections in an Onshape Project",
    )
    parser.add_argument(
        "-l", dest="link", help="Link of the project root document or main assembly"
    )
    parser.add_argument(
        "-n",
        dest="n_threads",
        required=False,
        default=10,
        help="Number of threads to use",
    )

    parser.add_argument("--cached", action="store_true")
    parser.add_argument(
        "--solver",
        required=False,
        choices=["barnesHut", "atlas2"],
        default="barnesHut",
        help="Graph solver model",
    )
    parser.add_argument(
        "--show_options", action="store_true", help="Show options on graph output"
    )

    parser.add_argument(
        "--save_graph", help="Save graph to the specified path", default=None
    )

    args = parser.parse_args()
    if not args.link and not args.cached:
        parser.error("Must either provide a link with '-l' or use the '--cached' flag")

    nthreads = int(args.n_threads)
    load_dotenv()
    if not args.cached:
        access_key: str = os.environ.get("ACCESS_KEY")
        private_key: str = os.environ.get("PRIVATE_KEY")

        # if args.cached:

        # https://formulaslug.onshape.com/documents/ec932fcb0efdb9716289a546/w/45ba9a6d4241901b0cc9d712/e/69389e018b58abaf464b3feb
        link_regex = (
            r"documents/(?P<document_id>.+)/w/(?P<workspace_id>.+)/e/(?P<element_id>.+)"
        )
        api = OnshapeAPI(access_key, private_key)
        if (match := re.search(link_regex, args.link)) is None:
            raise Exception("Couldn't parse link")

        elements = json.loads(
            api.document.get_elements(
                match.group("document_id"),
                "w",
                match.group("workspace_id"),
                element_id=match.group("element_id"),
            ).text
        )[0]

        match elements["type"]:
            case "Part Studio":
                doc_type = "Part"
            case "Assembly":
                doc_type = "Assembly"
            case _:
                raise Exception("Link does not point to a part studio or assembly")

        intitial_link = {
            "type": doc_type,
            "document_id": match.group("document_id"),
            "workspace_id": match.group("workspace_id"),
            "element_id": match.group("element_id"),
        }

        graph = networkx.DiGraph()

        to_visit = JoinableQueue()
        visited: set[tuple[str, str]] = set()

        to_visit.put(intitial_link)
        visited.add((intitial_link["document_id"], intitial_link["element_id"]))

        waiting = [False for _ in range(nthreads)]
        manager = multiprocessing.Manager()
        nodes = manager.list()
        edges = manager.list()

        graph_lock = multiprocessing.Lock()
        visited_lock = multiprocessing.Lock()
        waiting_lock = multiprocessing.Lock()
        processes = []
        for id in range(nthreads):
            processes.append(
                multiprocessing.Process(
                    target=process,
                    args=(
                        id,
                        waiting,
                        to_visit,
                        visited,
                        nodes,
                        edges,
                        graph_lock,
                        visited_lock,
                        waiting_lock,
                    ),
                )
            )

        for p in processes:
            p.start()
        to_visit.join()
        for p in processes:
            p.terminate()
            p.join(timeout=1.0)
        to_visit.close()

        for node in nodes:
            graph.add_node(node, label=node, group=node.split("|")[0])
        for edge1, edge2 in edges:
            graph.add_edge(edge1, edge2)

        # print("Finished Graph")
        # print(f"Graph Nodes: {graph.nodes}")
        # print(f"Graph Edges: {graph.edges}")

        networkx.write_gml(graph, "./network.gml")
    else:
        graph = networkx.read_gml("./network.gml")

    g = Network(
        height=1000,
        width="100%",
        bgcolor="#222222",
        font_color="white",
    )
    g.toggle_hide_edges_on_drag(False)
    match args.solver:
        case "barnesHut":
            g.barnes_hut()
        case "atlas2":
            g.force_atlas_2based()
    g.from_nx(graph)
    for node_id in g.get_nodes():
        node_degree = graph.degree[node_id]
        g.get_node(node_id)["size"] = (math.log(node_degree, 2) + 1) * 25
    if args.show_options:
        g.show_buttons()
    else:
        g.set_options("""
        const options = {
      "nodes": {

        "font": {
          "size": 80,
          "strokeWidth": 2
        }

      },
      "edges": {
        "arrows" : {
        "to": {
        "enabled" : true,
        "scaleFactor": 3.5
        }
        },
        "color": {
          "inherit": true
        },
        "font": {
          "size": 60,
          "face": "verdana"
        },

        "selfReferenceSize": null,
        "selfReference": {
          "angle": 0.7853981633974483
        },
        "smooth": {
          "forceDirection": "none"
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -80000,
          "springLength": 250,
          "springConstant": 0.001
        },
        "minVelocity": 0.75
      }
    }""")
    if args.save_graph:
        g.save_graph(args.save_graph)
    g.show("ex.html", notebook=False)
