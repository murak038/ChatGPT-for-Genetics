The goal of this coding challenge is to build a Natural Language Interface upon the Open Targets Platform GraphQL database, where the user can provide a question and a LLM converts the question into a query that can be run on the database.

I tried many experiment, which can be found in the `Workbook.ipynb` file with findings and analyses detailed. I will describe the final solution that I proposed, which can be run using `python query_opentargets.py`. 

Steps:
1. Initialize a conversation GPT instance with a `ConversationBufferMemory`
    * the `ConversationBufferMemory` allows the model to take feedback from the GraphQL API to improve generated query. 
2. Ask user for input
3. Create the prompt using the example provided in the repo
3. Query the LangChain bot to create a GraphQL query
4. Query the GraphQL database to get a list of hits or a possible error message. 
5. If there is an error message, generate a suggestion grounded within the schema. 
6. If the error persists more than 20 times, then we stop querying the LangChain application and don't return an answer.
7. If a valid GraphQL query is generated and returns results, the output of the GraphQL endpoint is parsed.


Improvements: 
* Use more examples to prompt the model: a multi-shot model is always better at generation than one-shot. 
* Use a different architecture: ChatGPT is great but a code specific model would remove a lot of hallucinations that the model output and improve error handling. 
* Connect the LangChain instance to the repo: We can embed the Git repo for Open Targets and run queries against that. 
* Embed the schema and use retrieval: we can embed the schema for the model and retrieve it as context for the generation. 

Notes: There are many instances where the above described method works and where it doesn't work. It would take a lot more work to get something deployable, but the ideal approach is something with a feedback loop. 
