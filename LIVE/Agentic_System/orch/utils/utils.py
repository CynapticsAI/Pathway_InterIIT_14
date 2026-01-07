import pathway as pw
from typing import Iterable
import json
import ast
from typing import List, Dict, Any, Optional

def _prepare_messages(
        messages: list[dict] | list[pw.Json] | pw.Json,
        ) -> list[dict]:
    
    if isinstance(messages, pw.Json):
        messages_as_list: Iterable[dict | pw.Json] = messages.as_list()
    else:
        messages_as_list = messages

    messages_decoded: list[dict] = [
        message.as_dict() if isinstance(message, pw.Json) else message
        for message in messages_as_list
    ]
    return messages_decoded

@pw.udf
def _get_final_output(messages: list[dict] | list[pw.Json] | pw.Json) -> str:
    messages_decoded = _prepare_messages(messages)
    last_out = messages_decoded[-1]
    last_out = json.loads(last_out['content'])['query']
    return last_out

@pw.udf
def _add_prompt(
        messages: list[dict] | list[pw.Json] | pw.Json,
        prompt : str = "You are a helpful assistant"
        ) -> list[dict]:
   
    messages_decoded = _prepare_messages(messages)
    if messages_decoded[0]['role'] == 'system':
        messages_decoded[0]['content'] = prompt
    else:
        messages_decoded.insert(0, {'role' : 'system', 'content' : prompt})
    return messages_decoded


@pw.udf
def _flip_roles(
        messages: list[dict] | list[pw.Json] | pw.Json,
        ) -> list[dict]:
    
    messages_decoded = _prepare_messages(messages)
    i = 0
    messages_decoded = messages
    message_length = len(messages_decoded)
    while i < message_length: 
        message = messages_decoded[i]

        if message['role'] == 'user':
            message['role'] = 'assistant'
            messages_decoded[i] = message
            i += 1
        
        elif message['role'] == 'assistant' and message.get('tool_calls', None):
            formatted_tool_outputs = []
            tool_call = messages_decoded.pop(i)
            while (messages_decoded[i]['role'] == 'tool'):
                formatted_tool_outputs.append(messages_decoded.pop(i))
            
            new_message = {'role' : 'assistant', 'content' : f"You called the tools <tools> {tool_call['tool_calls']} </tools>. Here were there outputs <tool_outputs> {formatted_tool_outputs} </tool_outputs>"}           
            messages_decoded.insert(i, new_message)
            message_length = len(messages_decoded)

        elif message['role'] == 'assistant':
            message['role'] = 'user'
            messages_decoded[i] = message
            i += 1
        
        else:
            i += 1
    
    return messages_decoded
@pw.udf
def _remove_context(messages: list[dict] | list[pw.Json] | pw.Json) -> list[dict]:
    messages_decoded = _prepare_messages(messages)
    last_message = json.loads(messages_decoded[-1]['content'])['query']
    return [{'role' : 'user', 'content' : last_message}]

@pw.udf
def _remove_clar_context(messages: list[dict] | list[pw.Json] | pw.Json) -> list[dict]:
    messages_decoded = _prepare_messages(messages)
    last_message = json.loads(messages_decoded[-1]['content'])['message']
    return [{'role' : 'user', 'content' : last_message}]

@pw.udf
def _add_context(output: list[dict] | list[pw.Json] | pw.Json, context : list[dict] | list[pw.Json] | pw.Json) -> list[dict]:
    context =  _prepare_messages(context)
    output = _prepare_messages(output)
    response = {'role' : 'assistant', 'content' : f"<agent_response> {str(output[-1]['content'])} </agent_reponse> "}
    context.append(response)
    return context

@pw.udf
def _add_chat(output: list[dict] | list[pw.Json] | pw.Json, context : list[dict] | list[pw.Json] | pw.Json) -> list[dict]:
    context =  _prepare_messages(context)
    output = _prepare_messages(output)
    response = {'role' : 'user', 'content' : f"{str(output[-1]['content'])}"}
    context.append(response)
    return context

def convert_string_to_list_of_dicts(data_string: str) -> Optional[List[Dict[str, Any]]]:
    if not isinstance(data_string, str):
        print(f"Error: Input must be a string, got {type(data_string)}")
        return None

    stripped_str = data_string.strip()
    
    try:
        parsed_data = json.loads(stripped_str)
        if isinstance(parsed_data, list) and all(isinstance(i, dict) for i in parsed_data):
            return parsed_data
    except json.JSONDecodeError:
        pass

    try:
        parsed_data = ast.literal_eval(stripped_str)
        if isinstance(parsed_data, list) and all(isinstance(i, dict) for i in parsed_data):
            return parsed_data
    except (ValueError, SyntaxError):
        pass

    print("Error: Could not parse string.")
    return None
@pw.udf
def _get_agent_call(messages: list[dict] | list[pw.Json] | pw.Json) -> str:
    messages_decoded = _prepare_messages(messages)
    last_out = messages_decoded[-1]
    last_out = json.loads(last_out['content'])['agent']
    return last_out
@pw.udf
def _get_route_call(messages: list[dict] | list[pw.Json] | pw.Json) -> str:
    messages_decoded = _prepare_messages(messages)
    last_out = messages_decoded[-1]
    last_out = json.loads(last_out['content'])['route']
    return last_out
@pw.udf
def _update_satisfied(messages: list[dict] | list[pw.Json] | pw.Json) -> str:
    messages_decoded = _prepare_messages(messages)
    last_out = messages_decoded[-1]
    last_out = json.loads(last_out['content'])['satisfied']
    return last_out

@pw.udf
def _get_final_output(messages: list[dict] | list[pw.Json] | pw.Json) -> str:
    messages_decoded = _prepare_messages(messages)
    last_out = messages_decoded[-1]
    last_out = json.loads(last_out['content'])['query']
    return last_out

@pw.udf
def _prepare_message_for_agent(
    messages: list[dict] | list[pw.Json] | pw.Json, 
    new_query: str
) -> list[dict]:
    """
    Appends the new sub-query as a special 'system' task message.
    """
    messages_decoded = _prepare_messages(messages)
    messages_decoded.append({
        "role": "system", 
        "content": f"AGENT_TASK: {new_query}"
    })
    return messages_decoded

AgentTopics = {
            "Agent A": "agent_A",
            "Agent B": "agent_B"
        }
