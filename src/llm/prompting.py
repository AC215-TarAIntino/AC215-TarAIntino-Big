# prompting.py
import os
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel, ChatSession, Content, Part

def main():
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("LOCATION", "us-central1")
    model_name = os.getenv("MODEL", "gemini-1.5-pro-002")

    if not project:
        raise ValueError("Missing GOOGLE_CLOUD_PROJECT env var.")

    vertex_init(project=project, location=location)
    model = GenerativeModel(model_name)
    chat: ChatSession = model.start_chat(history=[])
    print(f"Connected to Vertex AI model: {model_name} (project={project})")
    print("Type your message and press Enter. Type /exit to quit.\n")

    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[exit]")
            break
        if text.lower() in {"/exit", "/quit"}:
            break
        if not text:
            continue

        stream = chat.send_message(
            Content(parts=[Part.from_text(text)]),
            stream=True,
            generation_config={"temperature": 0.7, "max_output_tokens": 1024},
        )
        for chunk in stream:
            print(chunk.candidates[0].content.parts[0].text, end="", flush=True)
        print()

if __name__ == "__main__":
    main()

####################
# BUILD YOUR IMAGE #
####################

# docker build -t llm -f src/llm/Dockerfile .

######################
# RUN YOUR CONTAINER #
######################

# ./src/llm/docker-shell.sh

############################################################
# EXECUTE WITHIN YOUR CONTAINER TO ACCESS CHAT BOX WITH LLM#
############################################################

# python llm/prompting.py