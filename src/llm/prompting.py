# prompting.py — uses Vertex AI SDK for Gemini models (service account auth)
import os
from vertexai import init
from vertexai.preview.generative_models import GenerativeModel

def main():
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("LOCATION", "us-central1")
    model_name = os.getenv("MODEL", "gemini-2.5-pro")

    if not project:
        raise ValueError("Missing GOOGLE_CLOUD_PROJECT environment variable.")
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        raise ValueError("Missing GOOGLE_APPLICATION_CREDENTIALS environment variable.")

    # Initialize Vertex AI client
    init(project=project, location=location)
    model = GenerativeModel("gemini-2.5-pro")

    print(f"Connected to Vertex AI Gemini model: {model_name}")
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

        response = model.generate_content(
            text,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
            },
        )

        print(response.text, "\n")


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