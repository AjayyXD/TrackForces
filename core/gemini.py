import json
from google import genai
from google.genai import types
from . import stats 
from pydantic import BaseModel

class CodeforcesSuggestions(BaseModel):
    insights: list[str]
    suggestions: list[str]
    focus_topics: list[str]

class gemini_coach :

    @staticmethod
    def get_user_insights():

        stats_handler = stats.stats_handler()

        client = genai.Client()

        my_json_data = stats_handler.get_user_stats()
        config = types.GenerateContentConfig(
        system_instruction="You are a Codeforces coach. Analyze the user's statistics and provide concise tips. Keep each point under 60 characters. Maximum 2 insights, 2 suggestions, 3 focus topics.",
        response_mime_type="application/json",
        response_schema=CodeforcesSuggestions,
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=f"Here is the user stats in JSON format: {my_json_data}"),
                    types.Part.from_text(text="Please generate the tips and suggestions based on this data.")
                ]
            )
        ]

        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=contents,
            config=config
        )

        return response