from vector_store import open_vector_store


def search(query):
    with open_vector_store() as vector_store:
        retriever = vector_store.as_retriever(search_kwargs={"k": 2})
        return retriever.invoke(query)


if __name__ == "__main__":
    query = "컨테이너를 삭제해도 데이터를 유지하려면 어떻게 해야 하나요?"
    for document in search(query):
        print(document.page_content)
