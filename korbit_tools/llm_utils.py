import tiktoken

MODEL_NAME = "gpt-4"
BASE_TOKEN_PER_MESSAGE = 3

encoder = tiktoken.encoding_for_model(MODEL_NAME)


def estimate_token_count(messages: list[dict[str, str]]):
    num_tokens = 3  # every reply is primed with <|start|>assistant<|message|>
    for message in messages:
        num_tokens += BASE_TOKEN_PER_MESSAGE
        for value in message.values():
            num_tokens += count_token_string(value)
    return num_tokens


def count_token_string(content: str) -> int:
    return len(encoder.encode(content))


def truncate_string(content: str, threshold: int) -> str:
    """
    Truncate string until the threshold tokens is met, each iteration 
    remove 1000 characters from the string
    """
    token_count = count_token_string(content)
    while token_count > threshold:
        content = content[:-1000]
        token_count = count_token_string(content)
    return content
