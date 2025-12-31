import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

# Optional imports: if LangChain / Google GenAI packages are missing, we'll
# fall back to lightweight stubs so the transcript-fetch + local QA demo still runs.
try:
    from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import FAISS
    from langchain.schema import Document
    _HAS_LANGCHAIN = True
except Exception:
    ChatGoogleGenerativeAI = None
    GoogleGenerativeAIEmbeddings = None
    ChatPromptTemplate = None
    RecursiveCharacterTextSplitter = None
    FAISS = None
    Document = None
    _HAS_LANGCHAIN = False


# Load environment variables
load_dotenv()

# Initialize Gemini chat model and embeddings when available. If not available
# use fallback stub implementations so the app can run without those packages.
if _HAS_LANGCHAIN and ChatGoogleGenerativeAI is not None:
    model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=os.getenv("GOOGLE_API_KEY"))
else:
    class _StubResponse:
        def __init__(self, content: str):
            self.content = content

    class _StubModel:
        def invoke(self, prompt: str):
            return _StubResponse("[stub model] GenAI not available locally.\nPrompt was:\n" + str(prompt))

    model = _StubModel()

if _HAS_LANGCHAIN and GoogleGenerativeAIEmbeddings is not None:
    embedding = GoogleGenerativeAIEmbeddings(model="models/embedding-001", api_key=os.getenv("GOOGLE_API_KEY"))
else:
    embedding = None

# Get transcript from YouTube
def get_transcript(video_id):
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([t['text'] for t in transcript_list])
        return transcript
    except Exception as e:
        return f"Could not retrieve transcript: {e}"

# Chunk and embed transcript
def build_vectorstore(transcript):
    # If LangChain text splitter / FAISS are available, use them. Otherwise
    # create a very small fallback vectorstore that supports `similarity_search`.
    if _HAS_LANGCHAIN and RecursiveCharacterTextSplitter is not None and FAISS is not None and embedding is not None:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.create_documents([transcript])
        vectorstore = FAISS.from_documents(texts, embedding)
        return vectorstore

    # Fallback: split transcript into chunks and store as simple dicts
    chunks = []
    chunk_size = 1000
    for i in range(0, len(transcript), chunk_size):
        chunks.append(transcript[i:i+chunk_size])

    class SimpleVectorStore:
        def __init__(self, chunks):
            self.docs = [{"page_content": c} for c in chunks]

        def similarity_search(self, query, k=4):
            q = query.lower()
            scored = []
            for d in self.docs:
                # simple score: count occurrences of query tokens
                score = sum(d["page_content"].lower().count(token) for token in q.split())
                scored.append((score, d))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [s[1] for s in scored[:k]]

    return SimpleVectorStore(chunks)

# RAG retrieval and response generation
def generate_response_with_rag(vectorstore, question):
    docs = vectorstore.similarity_search(question, k=4)
    context = "\n\n".join([doc.page_content for doc in docs])

    system_template = "You are a helpful assistant that answers questions based on the following video transcript:\n\n{context}"
    user_template = "{question}"

    # If ChatPromptTemplate is available, build a prompt object; otherwise
    # pass a plain string to the model stub.
    if _HAS_LANGCHAIN and ChatPromptTemplate is not None:
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("user", user_template),
        ]).invoke({"context": context, "question": question})
    else:
        prompt = system_template.format(context=context) + "\n\n" + user_template.format(question=question)

    response = model.invoke(prompt)
    return getattr(response, "content", str(response))

# Main CLI loop
def main():
    video_id = input("Enter YouTube video ID: ").strip()
    question = input("Ask your question based on the video transcript: ").strip()

    transcript = get_transcript(video_id)
    if transcript.startswith("Could not"):
        print(transcript)
        return

    print("\nTranscript fetched successfully!")

    vectorstore = build_vectorstore(transcript)
    answer = generate_response_with_rag(vectorstore, question)

    print("\nAnswer from AI:")
    print(answer)

if __name__ == "__main__":
    main()
