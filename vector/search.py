from tools.files import scan_folder_recursive
from .chroma import query_chunks
def keyword_search(query, files):

    matches = []

    query = query.lower()

    for file in files:

        if query in file.lower():
            matches.append(file)

    return matches

def hybrid_search(query):

    semantic_results = vector_search(query)

    all_files = scan_folder_recursive(".")

    keyword_results = keyword_search(query, all_files)

    combined = list(set(semantic_results + keyword_results))

    return combined[:5]

def vector_search(query, n=5):

    results = query_chunks(query, n)

    # Chroma: results contain metadatas as a list of lists
    metadatas = results.get("metadatas", [[]])[0]
    files = []

    for meta in metadatas:
        if isinstance(meta, dict) and "file_path" in meta:
            files.append(meta["file_path"])

    return list(set(files))

    # Moorcheh version (commented out)
    # results = query_chunks(query, n)
    # files = [item["metadata"]["file_path"] for item in results["results"]]
    # return list(set(files))