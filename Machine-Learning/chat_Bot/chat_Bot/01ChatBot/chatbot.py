

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()


llm = HuggingFaceEndpoint(
    repo_id="mistralai/Mistral-7B-Instruct-v0.2",
    task="text-generation",
    # max_new_tokens=256,
    # temperature=0.3,
)

model = ChatHuggingFace(llm=llm)

chat_history = [SystemMessage(content="You are a concise AI assistant.")]

while True:
    user_input = input("You: -> ")
    if user_input.lower() == "exit":
        break

    chat_history.append(HumanMessage(content=user_input))

    prompt = "\n".join([msg.content for msg in chat_history])

    result = model.invoke(prompt)
    print("AI ->", result.content.strip())

    chat_history.append(SystemMessage(content=result.content.strip()))
