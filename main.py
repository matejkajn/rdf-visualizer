from streamlit_agraph import agraph, Node, Edge, Config
from rdflib import Graph, URIRef, Literal, BNode
import streamlit as st
import os


#  Function to delete all files in resource folder
def clear_resources():
    try:
        # Check if the 'resource' folder exists, and create it if not
        if not os.path.exists("resource"):
            os.makedirs("resource")

        # Get the list of files in the folder
        files = os.listdir("resource")

        # Iterate through the files and delete each one
        for file_name in files:
            file_path = os.path.join("resource", file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted: {file_path}")
    except Exception as e:
        st.toast(f"An error occurred: {e}")


# Function for saving file in resources
def save_file(file_name):
    clear_resources()
    with open(os.path.join("resource", file_name.name), "wb") as f:
        f.write(file_name.getbuffer())
        st.session_state['uploaded_file'] = file_name.name


# Function for processing SPARQL query
def return_query_graph(graph, query):
    result_graph = Graph()
    try:
        qres = graph.query(query)
    except Exception as e:
        st.error(
            f"An error occurred: {e}If you need help, check this documentation https://www.w3.org/TR/sparql11-query/. ")
        return False

    for row in qres:
        # Assuming each row contains a subject, predicate, and object
        try:
            s = row[0] if isinstance(
                row[0], (URIRef, BNode)) else URIRef(row[0])
            p = row[1] if isinstance(
                row[1], URIRef) else URIRef(row[1])
            o = row[2] if isinstance(
                row[2], (URIRef, Literal, BNode)) else Literal(row[2])

            result_graph.add((s, p, o))
        except IndexError:
            # Row does not have three elements, indicating it's not a full triplet
            continue

    return result_graph


# Main app
def app():
    st.header('RDF Graph Visualizer')

    #  Form for file upload and writing SPAQRL quries
    with st.form("upload-form", clear_on_submit=True):
        uploaded_file = st.file_uploader('Choose a file', accept_multiple_files=False,
                                         type=['nt', 'ttl', 'trig'],
                                         help='Choose a file',
                                         key="resource_file")

        sparql_query = st.text_area(
            label="Type in your SPARQL query.", key='sparql_query')

        st.warning('Write your SPARQL query to search for triples!', icon="🚨")

        submitted = st.form_submit_button('Render graph', type='primary')

        if 'uploaded_file' not in st.session_state:
            if submitted and uploaded_file is not None:
                save_file(uploaded_file)
                st.success(
                    'Your file has been succesfully uploaded!', icon='🥳')
            elif submitted and uploaded_file is None:
                st.error('An error occured while uploading your file.', icon="🚨")

    st.header('Graph')

    # Sidebar for configuration of generated graph
    with st.sidebar:
        st.header('Graph configurations')

        height = st.number_input(
            'Height', step=1, value=750, min_value=0, format='%d')
        width = st.number_input(
            'Width', step=1, value=750, min_value=0, format='%d')
        directed = st.checkbox('Directed', value=True)
        node_descriptions = st.checkbox('Node descriptions', value=False)
        edge_descriptions = st.checkbox('Edge descriptions', value=False)
        physics = st.checkbox('Physics', value=True)
        stabilize = st.checkbox('Stabilize', value=True)
        fit = st.checkbox('Fit', value=True)
        hierarchical = st.checkbox('Hierarchical', value=False)

        col1, col2, col3 = st.columns(3)
        with col1:
            subj_color = st.color_picker('Color of subject ', '#97C2FB')
        with col2:
            pred_color = st.color_picker('Color of predicator', '#F7A7A6')
        with col3:
            obj_color = st.color_picker('Color of object', '#97C2FB')

    config = Config(height=height,
                    width=width,
                    directed=directed,
                    physics=physics,
                    stabilize=stabilize,
                    fit=fit,
                    hierarchical=hierarchical)

    # Graph drawing or showing info div
    if 'uploaded_file' not in st.session_state:
        st.info('Upload your file above and try write some SPARQL query.', icon="ℹ️")
    else:
        g = Graph()

        with open('resource/' + st.session_state['uploaded_file'], 'rb') as file:
            g.parse(file)

        if st.session_state['sparql_query'] != "":
            if return_query_graph(g, sparql_query) != False:
                g = return_query_graph(g, sparql_query)
                if (len(g) <= 0):
                    st.warning(
                        'Application couldn\'t build visualizable graph from your SPARQL query.', icon="ℹ️")
                    return

        nodes = []
        edges = []

        existing_node_ids = set()

        for subj, pred, obj in g:
            # Create unique node IDs for literals by appending the language tag
            subj_id = str(subj)
            obj_id = str(obj) if not isinstance(obj, Literal) else str(
                obj) + "@" + obj.language if obj.language else str(obj)

            #  Add node descriptions
            if node_descriptions:
                subj_label = subj
                obj_label = obj
            else:
                subj_label = None
                obj_label = None

            # Subject nodes creation
            if subj_id not in existing_node_ids:
                subj_node = Node(id=subj_id, size=25,
                                 color=subj_color, label=subj_label)
                nodes.append(subj_node)
                existing_node_ids.add(subj_id)

            #  Object nodes creation
            if obj_id not in existing_node_ids:
                obj_node = Node(id=obj_id, size=25,
                                color=obj_color, label=obj_label)
                nodes.append(obj_node)
                existing_node_ids.add(obj_id)

            # Edge creation by connection of subject and object nodes
            if edge_descriptions:
                edges.append(Edge(source=subj_id, label=pred,
                                  target=obj_id, color=pred_color))
            else:
                edges.append(
                    Edge(source=subj_id, target=obj_id, color=pred_color))

        # Graph creation with arrays of nodes and edges
        agraph(nodes=nodes, edges=edges, config=config)

        if st.session_state['sparql_query'] != "":
            st.text_area("Your previous query.",
                         st.session_state['sparql_query'])


if __name__ == '__main__':
    app()
