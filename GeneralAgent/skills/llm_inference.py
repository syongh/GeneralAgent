from retrying import retry as _retry

class TinyDBCache():
    def __init__(self):
        from tinydb import TinyDB
        import os, json
        llm_path = os.environ.get('CACHE_PATH', None)
        if llm_path is None:
            from GeneralAgent.utils import get_server_dir
            llm_path = os.path.join(get_server_dir(), 'cache.json')
        self.db = TinyDB(llm_path)
        self.cache_llm = os.environ.get('LLM_CACHE', 'no') in ['yes', 'y', 'YES']
        self.cache_embedding = os.environ.get('EMBEDDING_CACHE', 'no') in ['yes', 'y', 'YES']

    def get(self, table, key):
        from tinydb import Query
        result = self.db.table(table).get(Query().key == key)
        if result is not None:
            return result['value']
        else:
            return None

    def set(self, table, key, value):
        from tinydb import Query
        self.db.table(table).upsert({'key': key, 'value': value}, Query().key == key)

    def set_llm_cache(self, key, value):
        if self.cache_llm:
            self.set('llm', key, value)

    def get_llm_cache(self, key):
        if self.cache_llm:
            return self.get('llm', key)
    
    def set_embedding_cache(self, key, value):
        if self.cache_embedding:
            self.set('embedding', key, value)

    def get_embedding_cache(self, key):
        if self.cache_embedding:
            return self.get('embedding', key)


global_cache = TinyDBCache()


def embedding_single(text) -> [float]:
    """
    embedding the text and return a embedding (list of float) for the string
    """
    global global_cache
    key = _md5(text)
    embedding = global_cache.get_embedding_cache(key)
    if embedding is not None:
        # print('embedding cache hitted')
        return embedding
    texts = [text]
    import openai
    resp = openai.Embedding.create(input=texts,engine="text-embedding-ada-002")
    result = [x['embedding'] for x in resp['data']]
    embedding = result[0]
    global_cache.get_embedding_cache(key, embedding)
    return embedding


def embedding_batch(texts) -> [[float]]:
    """
    embedding the texts(list of string), and return a list of embedding (list of float) for every string
    """
    global global_cache
    embeddings = {}
    remain_texts = []
    for text in texts:
        key = _md5(text)
        embedding = global_cache.get_embedding_cache(key)
        if embedding is not None:
            embeddings[text] = embedding
        else:
            remain_texts.append(text)
    if len(remain_texts) > 0:
        import openai
        resp = openai.Embedding.create(input=remain_texts, engine="text-embedding-ada-002")
        result = [x['embedding'] for x in resp['data']]
        for text, embedding in zip(remain_texts, result):
            key = _md5(text)
            global_cache.set_embedding_cache(key, embedding)
            embeddings[text] = embedding
    return [embeddings[text] for text in texts]


def cos_sim(a, b):
    import numpy as np
    from numpy.linalg import norm
    # This function calculates the cosine similarity (scalar value) between two input vectors 'a' and 'b' (1-D array object), and return the similarity.
    a = a if isinstance(a, np.ndarray) else np.array(a)
    b = b if isinstance(b, np.ndarray) else np.array(b)
    return np.dot(a, b)/(norm(a)*norm(b))


def search_similar_texts(focal:str, texts:[str], top_k=5):
    """
    search the most similar texts in texts, and return the top_k similar texts
    """
    embeddings = embedding_batch([focal] + texts)
    focal_embedding = embeddings[0]
    texts_embeddings = embeddings[1:]
    import numpy as np
    similarities = np.dot(texts_embeddings, focal_embedding)
    sorted_indices = np.argsort(similarities)
    sorted_indices = sorted_indices[::-1]
    return [texts[i] for i in sorted_indices[:top_k]]


def _md5(obj):
    import hashlib, json
    if isinstance(obj, str):
        return hashlib.md5(obj.encode('utf-8')).hexdigest()
    else:
        return hashlib.md5(json.dumps(obj).encode('utf-8')).hexdigest()


def _get_model(messages, model_type):
    import os
    from GeneralAgent import skills
    assert model_type in ['normal', 'smart', 'long']
    if model_type == 'normal' and skills.messages_token_count(messages) > 3000:
        model_type = 'long'
    model = os.environ.get('OPENAI_API_MODEL', 'gpt-3.5-turbo')
    if model_type == 'smart':
        model = 'gpt-4'
    if model_type == 'long':
        model = 'gpt-3.5-turbo-16k'
    return model

def _get_temperature():
    import os
    temperature = float(os.environ.get('TEMPERATURE', 0.5))
    return temperature


def llm_inference(messages, model_type='normal', stream=False, json_schema=None):
    """
    Run LLM (large language model) inference on the provided messages using the specified model.
    
    Parameters:
    messages: Input messages for the model, like [{'role': 'system', 'content': 'You are a helpful assistant'}, {'role': 'user', 'content': 'What is your name?'}]
    model_type: Type of model to use. Options are 'normal', 'smart', 'long'
    use_stream: Boolean indicating if the function should use streaming inference
    json_format: Optional JSON schema string

    Returns:
    If use_stream is True, returns a generator that yields the inference results as they become available.
    If use_stream is False, returns a string containing the inference result.
    If json_format is provided, the inference result is parsed according to the provided JSON schema and returned as a dictionary.

    Note:
    The total number of tokens in the messages and the returned string must be less than 4000 when model_variant is 'normal', and less than 16000 when model_variant is 'long'.
    """

    if stream:
        return _llm_inference_with_stream(messages, model_type)
    else:
        if json_schema is None:
            return _llm_inference_without_stream(messages, model_type)    
        else:
            import json
            if not isinstance(json_schema, str):
                json_schema = json.dumps(json_schema)
            messages[-1]['content'] += '\n' + return_json_prompt + json_schema
            # messages += [{'role': 'user', 'content': return_json_prompt + json_schema}]
            print(messages)
            result = _llm_inference_without_stream(messages, model_type)
            print(result)
            return json.loads(fix_llm_json_str(result))
        

def simple_llm_inference(messages, json_schema=None):
    """
    Run LLM (large language model) inference on the provided messages
    
    Parameters:
    messages: Input messages for the model, like [{'role': 'system', 'content': 'You are a helpful assistant'}, {'role': 'user', 'content': 'What is your name?'}]
    json_format: Optional JSON schema string

    Returns:
    If json_format is provided, the inference result is parsed according to the provided JSON schema and returned as a dictionary.
    Else return a string

    Note:
    The total number of tokens in the messages and the returned string must be less than 16000.
    """
    return llm_inference(messages, json_schema=json_schema)


@_retry(stop_max_attempt_number=3)
async def async_llm_inference(messages, model_type='normal'):
    import openai
    import logging
    global global_cache
    logging.debug(messages)
    key = _md5(messages)
    result = global_cache.get_llm_cache(key)
    if result is not None:
        return result
    model = _get_model(messages, model_type)
    temperature = _get_temperature()
    response = await openai.ChatCompletion.acreate(model=model, messages=messages, temperature=temperature)
    result = response['choices'][0]['message']['content']
    global_cache.set_llm_cache(key, result)
    return result


@_retry(stop_max_attempt_number=3)
def _llm_inference_with_stream(messages, model_type='normal'):
    """
    messages: llm messages, model_type: normal, smart, long
    """
    import openai
    import logging
    # from GeneralAgent import skills
    model = _get_model(messages, model_type)
    logging.debug(messages)
    global global_cache
    key = _md5(messages)
    result = global_cache.get_llm_cache(key)
    if result is not None:
        # print('llm_inference cache hitted')
        for x in result.split(' '):
            yield x + ' '
        yield '\n'
        # yield None
    else:
        temperature = _get_temperature()
        response = openai.ChatCompletion.create(model=model, messages=messages, stream=True, temperature=temperature)
        result = ''
        for chunk in response:
            if chunk['choices'][0]['finish_reason'] is None:
                token = chunk['choices'][0]['delta']['content']
                result += token
                global_cache.set_llm_cache(key, result)
                yield token
        # logging.info(result)
        # yield None


@_retry(stop_max_attempt_number=3)
def _llm_inference_without_stream(messages, model_type='normal'):
    import openai
    import logging
    global global_cache
    logging.debug(messages)
    # print(messages)
    key = _md5(messages)
    result = global_cache.get_llm_cache(key)
    if result is not None:
        return result
    model = _get_model(messages, model_type)
    temperature = _get_temperature()
    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
    result = response['choices'][0]['message']['content']
    global_cache.set_llm_cache(key, result)
    return result


def fix_llm_json_str(string):
    import json
    import re
    new_string = string.strip()
    if new_string.startswith('```json'):
        new_string = new_string[7:]
        if new_string.endswith('```'):
            new_string = new_string[:-3]
    try:
        json.loads(new_string)
        return new_string
    except Exception as e:
        print("fix_llm_json_str failed 1:", e)
        try:
            pattern = r'```json(.*?)```'
            match = re.findall(pattern, new_string, re.DOTALL)
            if match:
                new_string = match[-1]
            
            json.loads(new_string)
            return new_string
        except Exception as e:
            print("fix_llm_json_str failed 2:", e)
            try:
                new_string = new_string.replace("\n", "\\n")
                json.loads(new_string)
                return new_string
            except Exception as e:
                print("fix_llm_json_str failed 3:", e)
                
                messages = [{
                    "role": "system",
                    "content": """Do not change the specific content, fix the json, directly return the repaired JSON, without any explanation and dialogue.
                    ```
                    """+new_string+"""
                    ```"""
                }]

                message = llm_inference(messages)
                pattern = r'```json(.*?)```'
                match = re.findall(pattern, message, re.DOTALL)
                if match:
                    return match[-1]

                return message

return_json_prompt = """\n\nYou should only directly respond in JSON format without explian as described below, that must be parsed by Python json.loads.
Response JSON schema: \n"""


# def prompt_call(prompt_template, variables, json_schema=None):
#     from jinja2 import Template
#     import json
#     prompt = Template(prompt_template).render(**variables)
#     if json_schema is not None:
#         prompt += return_json_prompt + json_schema
#         result = llm_inference([{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'system', 'content': prompt}], model_type='smart')
#         return json.loads(fix_llm_json_str(result))
#     else:
#         result = llm_inference([{'role': 'system', 'content': prompt}], model_type='smart')