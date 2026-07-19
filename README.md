# Local Data Analyst Agent

This workspace now contains a lightweight Streamlit app for uploading a CSV file and generating a business-focused analysis using a GitHub Copilot/OpenAI-compatible API token.

## Run locally

1. Install dependencies:
   ```bash
   python3 -m pip install --user -r requirements.txt
   ```
2. Start the app:
   ```bash
   streamlit run app.py
   ```
3. Open the local URL shown in the terminal.

## Notes

- Set your token in the UI or via the OPENAI_API_KEY environment variable.
- The app supports both GitHub Models-style tokens and OpenAI-compatible API keys with the `gpt-4o-mini` model.
