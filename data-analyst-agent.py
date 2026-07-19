from app import DataAnalystAgent


if __name__ == "__main__":
    api_key = input("Enter your GitHub Copilot / OpenAI API token: ")
    print("This entrypoint now launches the same logic used by the Streamlit UI.")
    print("Run the app locally with: python3 -m streamlit run app.py")
    agent = DataAnalystAgent(api_key)
    print("Agent ready. Upload a CSV in the Streamlit UI to begin.")

