# Jarvis FEC — Assistente MCP

Demo de assistente de voz que usa **MCP (Model Context Protocol)** para controlar
o sistema operacional: abrir aplicativos, ajustar volume, listar/abrir arquivos.

## Arquitetura

```
[Navegador: HUD + microfone]  --HTTP-->  [jarvis_backend.py: FastAPI + Ollama]
                                                   |                |
                                                   |          (Ollama local,
                                                   |           porta 11434)
                                            (conexão MCP via stdio)
                                                   |
                                       [mcp_system_server.py: ferramentas]
```

1. Você fala no navegador (Web Speech API transcreve pra texto).
2. O texto vai pro backend, que manda pro modelo local (via Ollama) junto
   com a lista de ferramentas disponíveis no servidor MCP.
3. O modelo decide se/qual ferramenta chamar (`open_app`, `set_volume`, etc).
4. O backend executa a ferramenta via MCP e devolve o resultado pro modelo.
5. O modelo formula a resposta final, que é falada em voz alta no navegador.

100% local: depois do modelo baixado, não precisa de internet nem de chave
de API — ótimo pra feira, onde wifi costuma ser instável.

## Setup

**1) Instale o Ollama** (uma vez só): https://ollama.com/download

**2) Baixe um modelo com suporte a tool calling:**

```bash
ollama pull qwen3:8b
```

Precisa de ~8GB de RAM/VRAM livres. Se o PC for mais fraco, use um modelo
menor (edite `MODEL` em `jarvis_backend.py` também):

```bash
ollama pull qwen3:4b
# ou, ainda mais leve:
ollama pull llama3.2:3b
```

Quanto menor o modelo, menos confiável tende a ser o tool calling — teste
com antecedência.

**3) Instale as dependências Python:**

```bash
cd jarvis-fec
python -m venv venv
# Linux/Mac: source venv/bin/activate
# Windows: venv\Scripts\activate

pip install -r requirements.txt

# Se for Windows e quiser controle de volume:
pip install pycaw comtypes

# Se quiser a ferramenta de screenshot:
pip install pyautogui
```

O Ollama normalmente já roda como serviço em segundo plano depois da
instalação. Se o backend não conseguir conectar, rode `ollama serve` num
terminal separado antes do próximo passo.

## Rodar

```bash
python jarvis_backend.py
```

Depois abra `frontend/index.html` no **Chrome** (a Web Speech API funciona
melhor nele). Clique no anel pra falar.

## ⚠️ Testar ANTES do dia da feira

- `open_app`: os nomes de app variam por SO. No Windows teste com o nome exato
  (`notepad`, `calc`, `chrome` — às vezes precisa do caminho completo). No
  Linux, precisa ser o nome do binário (`gedit`, `firefox`).
- `set_volume`: no Windows precisa do `pycaw` instalado; no Linux precisa do
  `pactl` (PulseAudio/PipeWire) disponível.
- Teste o microfone no PC/navegador que vai usar na feira — ambientes com
  barulho podem atrapalhar o reconhecimento de voz.
- **Teste no PC exato que vai levar pra feira**, com o modelo já baixado.
  Modelos menores (7-8B) às vezes "esquecem" de chamar a ferramenta e só
  respondem em texto — se isso acontecer no teste, ajuste o
  `SYSTEM_PROMPT` deixando ainda mais explícito ("sempre use uma ferramenta
  quando o pedido envolver o computador") ou troque pra `qwen3:8b` se
  estiver usando um modelo menor.
- A primeira resposta depois de abrir o Ollama costuma ser mais lenta
  (carregando o modelo na memória) — rode um comando de "aquecimento" antes
  da plateia chegar.
- Tenha **2-3 comandos testados e garantidos** pra puxar durante a
  apresentação, em vez de improvisar.

## Roteiro sugerido de demo

1. "Jarvis, liste os arquivos da minha área de trabalho"
2. "Jarvis, abra a calculadora"
3. "Jarvis, diminua o volume para 20%"
4. (opcional) "Jarvis, tire um print da tela"

Enquanto isso, explique pro público: cada um desses comandos foi resolvido
por uma **ferramenta MCP diferente** — o mesmo Claude, sem saber nada sobre o
seu PC de antemão, descobriu dinamicamente quais ferramentas existem e como
usá-las. É exatamente esse o problema que o MCP resolve: um jeito padronizado
de IA conversar com aplicações, em vez de cada integração ser feita na mão.

## Ideias de expansão (se sobrar tempo)

- Adicionar um segundo servidor MCP (ex: Spotify, clima via web search)
- Mostrar no HUD, em tempo real, qual ferramenta está sendo chamada (o campo
  `tool_calls` da resposta já vem pronto pra isso)
- Trocar o círculo do HUD por uma versão em Three.js, tipo o Jarvis do filme