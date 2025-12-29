The four secrets:
1. Gemini API key 
2. Model name
2. Qdrant Cloud url and API key
3. Embedding model name and dimensions

We have stored these in an env file, python can't use these directly yet, we need these in our python code alongside validation, a clean way to access them throughout our app

To solve this problem, we use Pydantic settings(the standard FastAPI pattern) which reads the env file automatically, validates that the required values exist and are of the right type, providing us with a settings object that can be imported anywhere

1. When you initialize the Gemini client → needs settings.gemini_api_key
2. When you connect to Qdrant → needs settings.qdrant_url and settings.qdrant_api_key
3. When you load the embedding model → needs settings.embedding_model_name
4. When you create the Qdrant collection → needs settings.embedding_dimension

What is Pydantic? - It is a python library used for data validation using python type annotations, ensuring types match and other constraints. - The core idea is to define a class with type hints and Pydantic validates and converts data to match those types

What about Pydantic Settings? - An extension specifically for configuration management. Adds automatic environment variable loading, case-insensitive matching, nesting config support, default values

FastAPI uses Pydantic extensively - Request and response validation, settings management, type hints provide automatic API documentation

Make sure to install using a venv to activate .\venv\Scripts\Activate.ps1

You can install the packages using pip install -r requirements.txt and update requirements using pip freeze > requirements.txt