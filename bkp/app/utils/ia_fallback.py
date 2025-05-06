from app.utils.ollama import chamar_ollama as chamar_ollama_completo

async def chamar_ollama(prompt: str, telefone: str) -> tuple[str, list]:
    resposta, tokens = await chamar_ollama_completo(prompt, telefone)
    return resposta, tokens
