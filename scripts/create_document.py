from mcpbot.shared.init import config
from mcpbot.shared.utils import read_file


WRITE = False

db_vector = config.databases.vector
if WRITE:
    for document in read_file("faq.yml"):
        id = document["title"]

        text = (
            f"Source: {document['source']}\n"
            f"Title: {document['title']}\n"
            f"Question: {document['question']}\n"
            f"Answer: {document['answer']}"
        )
        metadata = {
            "title": document["title"],
            "category": document["category"],
            "source": document["source"],
            "question": document["question"],
        }
        db_vector.upsert(id=id, text=text, metadata=metadata)
else:
    search = db_vector.search(question="Parking", method="cosine", n_docs=1)
    print(search)
