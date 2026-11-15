import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI
from prompts import system_prompt
from call_function import available_functions, call_function


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("user_prompt", help="The prompt to send to the AI")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    if args.verbose:
        print(f"User prompt: {args.user_prompt}")

    api_key = os.environ.get("OPENROUTER_API_KEY")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": args.user_prompt},
    ]

    for _ in range(20):
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            tools=available_functions,
            temperature=0,
        )

        if args.verbose and response.usage:
            print(f"Prompt tokens: {response.usage.prompt_tokens}")
            print(f"Response tokens: {response.usage.completion_tokens}")

        message = response.choices[0].message

        # Save the assistant's response in conversation history
        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                result_message = call_function(tool_call, args.verbose)

                if not result_message["content"]:
                    raise Exception("Function call returned empty content")

                # Save the tool result in conversation history
                messages.append(result_message)

                if args.verbose:
                    print(f"-> {result_message['content']}")
        else:
            print("Final response:")
            print(message.content)
            return

    print("Error: Maximum iterations reached without a final response.")
    exit(1)


if __name__ == "__main__":
    main()
