import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

KB_PATH = os.path.join(os.path.dirname(__file__), "knowledge_base.txt")

with open(KB_PATH, "r", encoding="utf-8") as file:
    text = file.read()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len,
    separators=["\n\n", "\n", " ", "", ".", "!", "?", ",", ":", ";", "---"],
)
chunks = text_splitter.split_text(text)
ids = [str(i) for i in range(len(chunks))]

client = chromadb.Client()
russian_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
collection = client.get_or_create_collection(
    "terraria_guide", embedding_function=russian_ef
)
if collection.count() == 0:
    collection.add(documents=chunks, ids=ids)


def retrieve(query: str, n_results: int = 3) -> str:
    results = collection.query(query_texts=[query], n_results=n_results)
    documents = (results.get("documents") or [[]])[0]
    return "\n\n".join(documents)


if __name__ == "__main__":
    query = "Как победить Плантеру?"
    print(retrieve(query))
