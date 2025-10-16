# prompting.py  — uses google-genai SDK for Gemini 2.x models
import os
from google import genai

def main():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY environment variable.")

    client = genai.Client(api_key=api_key)
    model = os.getenv("MODEL", "gemini-2.5-pro")

    print(f"Connected to Google GenAI model: {model}")
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

        response = client.models.generate_content(
            model=model,
            contents=text,
            config={
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