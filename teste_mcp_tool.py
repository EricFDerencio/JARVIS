import asyncio
from ollama import AsyncClient


async def main():
    client = AsyncClient()

    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "Lista arquivos e pastas de um diretório.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Diretório a listar."
                        }
                    },
                    "required": []
                }
            }
        }
    ]

    print("Chamando Ollama...", flush=True)

    response = await client.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "user",
                "content": "Liste os arquivos do diretório atual."
            }
        ],
        tools=tools,
    )

    print("Ollama respondeu!", flush=True)
    print(response)


if __name__ == "__main__":
    asyncio.run(main())