import pathway as pw
from typing import Iterable


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
def _add_message_format(query : str) -> list[dict]:
    return [{"role" : "user", "content" : query}]


@pw.udf
def _remove_message_format(
        messages: list[dict] | list[pw.Json] | pw.Json,
        ) -> str:
    messages_decoded = _prepare_messages(messages)
    last_message = messages_decoded[-1]
    return last_message['content']


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

if __name__ == '__main__':
    messages = [
  {
    "role": "system",
    "content": "You are ChatGPT, a helpful assistant that can perform computations using Python when needed."
  },
  {
    "role": "user",
    "content": "Calculate the mean and variance of the numbers [3, 5, 7, 9, 11] and plot a histogram."
  },
  {
    "role": "assistant",
    "content": None,
    "tool_calls": [
      {
        "id": "call_01",
        "type": "python",
        "function": "analyze_numbers",
        "arguments": {
          "numbers": [3, 5, 7, 9, 11]
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_01",
    "content": "Mean = 7.0, Variance = 8.0. Histogram saved as hist.png"
  },
  {
    "role": "assistant",
    "content": "The mean of the list is **7.0**, and the variance is **8.0**. I’ve also created and saved a histogram as `hist.png`."
  },
  {
    "role": "user",
    "content": "Now calculate the standard deviation of the same list."
  },
  {
    "role": "assistant",
    "content": None,
    "tool_calls": [
      {
        "id": "call_02",
        "type": "python",
        "function": "compute_std",
        "arguments": {
          "numbers": [3, 5, 7, 9, 11]
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_02",
    "content": "Standard deviation = 2.8284271247461903"
  },
  {
    "role": "assistant",
    "content": "The standard deviation of the numbers is approximately **2.83**."
  }
]
    
    print(_flip_roles(messages))





