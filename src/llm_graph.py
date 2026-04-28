import json
from openai import OpenAI
from src.graph_prompt import build_graph_prompt


def generate_graph_data(record, api_key):
    client = OpenAI(api_key=api_key)

    prompt = build_graph_prompt(record)

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    output_text = response.choices[0].message.content

    return json.loads(output_text)