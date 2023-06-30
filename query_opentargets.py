import openai
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

import os
import re
import json
import requests
import openai
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

def query_chatgpt(prompt):
    response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
                {"role": "system", "content": "You are an expert assistant that can turn user queries into GraphQL queries."},
                {"role": "user", "content": prompt}
            ],
          temperature=0,
          max_tokens=1024,
          top_p=1,
          frequency_penalty=0,
          presence_penalty=0,
            stop=["###"],
        )
    response_text = response.choices[0].message['content']
    return response_text

# swap the chatGPT model to enable extra long context
def query_chatgpt_16k(prompt):
    ## Function to 
    response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo-16k",
          messages=[
                {"role": "system", "content": "You are an expert assistant that can turn user queries into GraphQL queries."},
                {"role": "user", "content": prompt}
            ],
          temperature=0,
          max_tokens=1024,
          top_p=1,
          frequency_penalty=0,
          presence_penalty=0,
            stop=["###"],
        )
    response_text = response.choices[0].message['content']
    return response_text

def query_langchain(llm, prompt):
    response = llm.predict(input=prompt)
    return response

def query_graphql(query_string):
    error_message, hits_list = None, None
    # Set base URL of GraphQL API endpoint
    base_url = "https://api.platform.opentargets.org/api/v4/graphql"

    # Perform POST request and check status code of response
    # This handles the cases where the Open Targets API is down or our query is invalid
    try:
        response = requests.post(base_url, json={"query": query_string})
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        a = 1
    # Transform API response from JSON into Python dictionary and print in console
    api_response = json.loads(response.text)
    if 'data' not in api_response:
        error_message = api_response
        # print('ERROR:\n {}\n\n'.format(error_message))
    elif api_response['data']==None:
        error_message = api_response['errors'][0]['message']
        # print('ERROR:\n {}\n\n'.format(error_message))
    else:
        try:
            hits_list = api_response["data"]["search"]["hits"][0]
        except:
            print(api_response)
    
    return error_message, hits_list

def convert_json_response(hits_list, user_input):
    response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
                {"role": "system", "content": "You are an helpful assistant."},
                {"role": "user", "content": "Given the following json response, answer the question as a list. Json Response:\n{}\n\nQuestion:\n{}".format(hits_list, user_input)}
            ],
          temperature=0,
          max_tokens=1024,
          top_p=1,
          frequency_penalty=0,
          presence_penalty=0,
            stop=["###"],
        )
    response_text = response.choices[0].message['content']
    return response_text

if __name__=="__main__":
    # read Open AI API key from environment variable
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    # read prompt template file
    with open("graphql_schema.txt", "r") as f:
        prompt_template = f.read()

    # read in GraphQL schema
    with open("graphql_real_schema.txt", "r") as f:
        schema = f.read()

    # Prime the target query for completion
    prime_prompt = "query top_n_associated_diseases {\n  search(queryString:"

    # Custom input by the user
    # user_input = "Find the top 2 diseases associated with BRCA1"
    user_input = input("How can I help you today?\n")

    # initialize OpenAI model
    chat = OpenAI(temperature=0.2, top_p=0.1 ,openai_api_key=openai.api_key)
    llm = ConversationChain(
        llm=chat, 
        memory=ConversationBufferMemory(), 
        verbose=False
    )
    # create the prompt
    prompt = "Given the following example, create the GraphQL query to answer the following user input. If a number isn't given, return all possible answers. {}\n\nUser Input: {}\n\nGenerated Query:\n".format(prompt_template, user_input)
    # query the langchain bot
    query_string = query_langchain(llm, prompt)

    # query graphql
    error_message, hits_list = query_graphql(query_string)
    runs = 0
    
    while error_message:
        if 'syntaxError' not in error_message:
            # if its not a syntax error, we can ask GPT for suggestions
            prompt = "Given a query, error message and schema, generate a suggestion on how the query can be improved in natural language citing specific fields within the schema. Generate only a suggestion, not a query.\nSchema:\n{} \nQuery:\n{}\nError Message:\n{}Suggestion:\n".format(schema, query_string, error_message)
            suggestion = query_chatgpt_16k(prompt)
            # print(suggestion)
            prompt = "The query failed with the following error: {}\n Here is a suggestion on how to correct the query. {} Can you regenerate the query to fix the error? \nRegenerated Query:\n".format(error_message, suggestion)
        
        else:
            # suggestions on syntax errors confuse the model
            prompt = "The query failed with the following error: {}\n Can you regenerate the query to fix the error? \nRegenerated Query:\n".format(error_message)
        query_string = query_langchain(llm, prompt)
        error_message, hits_list = query_graphql(query_string)
        runs+=1
        if runs==20:
            error_message=None
            break

    # convert 
    if hits_list:
        # convert json response into 
        response_text = convert_json_response(hits_list, user_input)    
    # print(hits_list)
        print('ANSWER:\n{}'.format(response_text))
    else:
        print('No Answer Found :/')