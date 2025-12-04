def build_prompt(contexts, question):
    system = (
        "Tu es Rafiq-AI, un assistant pour le 'Défi national Nuit de l'Info 2025'.\n"
        "Utilise uniquement les informations fournies dans les sections 'CONTEXT' ci-dessous.\n"
        "Si la réponse n'est pas contenue dans le contexte, dis clairement que tu n'as pas l'information.\n\n"
    )
    prompt = system
    for i, c in enumerate(contexts, start=1):
        prompt += f"[CONTEXT {i}]\n{c}\n\n"
    prompt += f"Question: {question}\nAnswer concisely in French. Cite la source entre crochets si possible.\n"
    return prompt
