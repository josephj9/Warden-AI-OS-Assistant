from tools.files import scan_folder_recursive
from .moorcheh import query_chunks
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

    # Chroma version (commented out)
    # metadatas = results["metadatas"][0]
    # files = []
    # for meta in metadatas:
    #     files.append(meta["file_path"])
    # return list(set(files))

    # Moorcheh version
    files = [item["metadata"]["file_path"] for item in results["results"]]

    return list(set(files))