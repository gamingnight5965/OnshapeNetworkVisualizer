# Onshape Graph Visualizer
Visualization tool for connections between Onshape documents.

# How to Use
1. Install required packages using `requirements.txt`
2. Create an Onshape API Key using the [Onshape Developer Portal](https://cad.onshape.com/appstore/dev-portal/apiKeys)
3. Add your `ACCESS_KEY` and `PRIVATE_KEY` to your `.env` file
4. run `pyhton -m onshape-graph-visualizer -l <link_to_root_assembly>`
5. After running the program once with a link you can use `--cached` instead to load the saved network.

# Advanced Options
```
usage: Onshape Graph Visualizer [-h] [-l LINK] [-n N_THREADS] [--cached]
                                [--solver {barnesHut,atlas2}] [--show_options]
                                [--save_graph SAVE_GRAPH]

Creates a visualization of the connections in an Onshape Project

options:
  -h, --help            show this help message and exit
  -l LINK               Link of the project root document or main assembly
  -n N_THREADS          Number of threads to use
  --cached
  --solver {barnesHut,atlas2}
                        Graph solver model
  --show_options        Show options on graph output
  --save_graph SAVE_GRAPH
                        Save graph to the specified path
```
