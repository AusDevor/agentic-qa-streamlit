import requests
import json
from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

base_url = "https://llm-services.staging.chatbot.johnsnowlabs.dev/docqa/docqa"
id="docqa-7aeff720-9e4d-4c70-addd-081afd29b45e"

headers = {
    'x-api-key': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYzhlZjdkYjMtZGM5Mi00YmU3LThlYzUtMzEzOTkwYzU3ODJlIn0.gpHhu3Iy9GlcImR_AD3r8zLLZS5mJMbnfuavGnqUo8KvAQGglreNRaPA-C01ATf4v4EC9N6r17FUQhpwjWfUh3i6omyI2bzppWYNV_HLQbNQBDJ9gr5MUYqH8aKs9koTDOcuzXPpsmek8SHu3iwebuO8WQpC2SzmueWojYmUTm_TsILf_9QQunfGrkgCNM289jibw18qJSdRJEbsGvMjHpzXFTC_03R3zaZ_bmJbAJlA3jSq7041Uo1Pw8DkoQkrloZqZ-fOEz9opr-TVGyzGI768hVtGl1gL6fkXeAjdjcEnehnd1wkvWbCPksnZRkakyA51YtmDI6gkUwFl1gFDw',
    'Authorization': 'Basic YWRtaW46ZGJaY04zcDU5Q0t6bEpmWg==',
    'Content-Type': 'application/json'
}
headers2 = {
  'x-api-key': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYzhlZjdkYjMtZGM5Mi00YmU3LThlYzUtMzEzOTkwYzU3ODJlIn0.gpHhu3Iy9GlcImR_AD3r8zLLZS5mJMbnfuavGnqUo8KvAQGglreNRaPA-C01ATf4v4EC9N6r17FUQhpwjWfUh3i6omyI2bzppWYNV_HLQbNQBDJ9gr5MUYqH8aKs9koTDOcuzXPpsmek8SHu3iwebuO8WQpC2SzmueWojYmUTm_TsILf_9QQunfGrkgCNM289jibw18qJSdRJEbsGvMjHpzXFTC_03R3zaZ_bmJbAJlA3jSq7041Uo1Pw8DkoQkrloZqZ-fOEz9opr-TVGyzGI768hVtGl1gL6fkXeAjdjcEnehnd1wkvWbCPksnZRkakyA51YtmDI6gkUwFl1gFDw',
  'Authorization': 'Basic YWRtaW46ZGJaY04zcDU5Q0t6bEpmWg=='
}


def createDocQA():
    create_doc_payload = json.dumps({})
    response = requests.request("POST", base_url, headers=headers, data=create_doc_payload)
    
    return json.loads(response.text)

def addFile(files):
    url = f"{base_url}/files/{id}"
    payload={}
    response = requests.post(url, headers=headers2, data=payload, files=files)

    return response.text

def call_llm(query, context):
    prompt = f"Give me answer for this question based on context provided:\n\nQuestion:{query} Context:{context}"

    completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {
            "role": "user",
            "content": prompt,
        },
    ],
    )

    summary = completion.choices[0].message.content.strip()

    return summary
    
def get_splits(query):
    url=f"{base_url}/query/{id}"
    payload = json.dumps({
        "query": query,
        "top_k": 30,
        "threshold": 0.0001,
        "include_meta": True,
        "knn_candidates": 10000
    })
    
    response = requests.post(url, headers=headers, data=payload)
    
    return json.loads(response.text)

def get_answer(query):
    splits = get_splits(query)
    split_texts = [split['text'] for split in splits['results']]
    context = split_texts[0]
    return call_llm(query, context)
