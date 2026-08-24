"""
Jarvis Backend — versão Ollama (100% local, sem custo, sem internet)
======================================================================
Host MCP: conecta um modelo local via Ollama (tool calling) com o servidor
MCP de sistema (mcp_system_server.py) e expõe um endpoint HTTP simples que
o frontend (HUD + Web Speech API) chama.

Setup:
    1) Instale o Ollama: https://ollama.com/download
    2) Baixe um modelo com suporte a tool calling:
           ollama pull qwen3:8b
       (precisa de ~8GB de RAM/VRAM livres; se o PC for mais fraco, use
       qwen3:4b ou llama3.2:3b — suporte a tools mais fraco, mas roda leve)
    3) pip install -r requirements.txt
    4) python jarvis_backend.py

O Ollama precisa estar rodando (normalmente inicia sozinho como serviço
depois da instalação; se não, rode `ollama serve` num terminal separado).

O frontend (frontend/index.html) faz POST em http://localhost:8000/command
"""
import sys
import json
from contextlib import AsyncExitStack
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ollama import AsyncClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "qwen3:8b"  # troque por qwen3:4b ou llama3.2:3b se o PC for mais fraco
SYSTEM_PROMPT = (
    "Você é o Jarvis, um assistente de IA que roda no computador do usuário "
    "e controla o sistema através de ferramentas. Seja direto, confirme as "
    "ações que executou, e responda sempre em português do Brasil, em "
    "frases curtas (a resposta será falada em voz alta). Não explique seu "
    "raciocínio, só aja e responda."
)

ollama_client = AsyncClient()  # conecta no Ollama local (http://localhost:11434)

app = FastAPI(title="Jarvis Backend (Ollama)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global da sessão MCP (mantida viva enquanto o servidor roda)
_stack: AsyncExitStack | None = None
_session: ClientSession | None = None
_tools_ollama_format: list[dict[str, Any]] = []


class CommandRequest(BaseModel):
    text: str


class CommandResponse(BaseModel):
    reply: str
    tool_calls: list[str] = []


@app.on_event("startup")
async def startup():
    global _stack, _session, _tools_ollama_format

    _stack = AsyncExitStack()
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_system_server.py"],
    )
    read, write = await _stack.enter_async_context(stdio_client(server_params))
    _session = await _stack.enter_async_context(ClientSession(read, write))
    await _session.initialize()

    tools_result = await _session.list_tools()
    _tools_ollama_format = [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.input_schema,
            },
        }
        for t in tools_result.tools
    ]
    print(f"[jarvis] Conectado ao MCP. Ferramentas: {[t['function']['name'] for t in _tools_ollama_format]}")
    print(f"[jarvis] Usando modelo Ollama: {MODEL}")


@app.on_event("shutdown")
async def shutdown():
    if _stack:
        await _stack.aclose()


@app.post("/command", response_model=CommandResponse)
async def command(req: CommandRequest):
    assert _session is not None

    print(f"\n[jarvis] Comando recebido: {req.text}", flush=True)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.text},
    ]

    tool_calls_log: list[str] = []

    for iteration in range(6):
        print(
            f"[jarvis] Iteração {iteration + 1}: chamando Ollama...",
            flush=True,
        )

        response = await ollama_client.chat(
            model=MODEL,
            messages=messages,
            tools=_tools_ollama_format,
            think= False,
        )

        print("[jarvis] Ollama respondeu.", flush=True)

        msg = response["message"]

        print(
            f"[jarvis] Conteúdo: {msg.get('content', '')[:200]}",
            flush=True,
        )

        tool_calls = msg.get("tool_calls") or []

        print(
            f"[jarvis] Tool calls encontradas: {len(tool_calls)}",
            flush=True,
        )

        if not tool_calls:
            return CommandResponse(
                reply=msg.get("content", ""),
                tool_calls=tool_calls_log,
            )

        messages.append({
            "role": "assistant",
            "content": msg.get("content", ""),
            "tool_calls": tool_calls,
        })

        for call in tool_calls:
            fn = call["function"]
            name = fn["name"]
            args = fn.get("arguments") or {}

            print(
                f"[jarvis] Executando MCP: {name}({args})",
                flush=True,
            )

            tool_calls_log.append(
                f"{name}({json.dumps(args, ensure_ascii=False)})"
            )

            result = await _session.call_tool(name, args)

            print(
                f"[jarvis] MCP respondeu: {result}",
                flush=True,
            )

            result_text = "".join(
                c.text
                for c in result.content
                if hasattr(c, "text")
            )

            print(
                f"[jarvis] Resultado da ferramenta: {result_text[:500]}",
                flush=True,
            )

            messages.append({
                "role": "tool",
                "content": result_text,
            })

    return CommandResponse(
        reply="Desculpa, me perdi tentando executar isso. Pode repetir de outro jeito?",
        tool_calls=tool_calls_log,
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
