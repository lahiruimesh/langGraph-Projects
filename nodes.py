import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    #temperature=0,
    #groq_api_key=os.getenv("GROQ_API_KEY")
)

def input_node(state):
    topic = input("Enter a topic for a quote: ")

    return{
        "topic": topic
    }

def generate_quote_node(state):
    topic = state["topic"]

    prompt = f"""
    Give a short motivational quote about {topic}.
    Only return the quote.
    """

    response = llm.invoke(prompt)

    return {
        "quote": response.content
    }

def output_node(state):
    print("\nGenerated Quote:")
    print(state["quote"])

    return {}