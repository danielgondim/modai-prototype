# Arquitetura do Chatbot ModAI e Otimização de Tokens

Este documento detalha as decisões arquiteturais adotadas no fluxo de inteligência artificial do ModAI, com foco especial na orquestração via LangGraph, RAG (Retrieval-Augmented Generation) e nas agressivas estratégias de economia de tokens implementadas para viabilizar o chatbot como um produto SaaS escalável.

## 1. Arquitetura do Fluxo Conversacional (LangGraph)

O chatbot não opera com uma única chamada estática ao LLM. Ao invés disso, o fluxo é orquestrado como um grafo de estados usando a biblioteca **LangGraph**, dividindo as responsabilidades em pequenos "nós" (nodes) especialistas.

### Nós do Grafo (Pipeline de Mensagem)
1. **Verificação de Cache Semântico (`check_cache`)**: Verifica no Redis se o usuário fez uma pergunta idêntica/similar recentemente. Se sim, retorna o cache e economiza 100% dos tokens da LLM.
2. **Classificador de Intenção (`classify_intent`)**: Usa um modelo ultraleve/barato para definir se a mensagem atual exige busca no banco de dados (RAG) ou se é uma interação direta (ex: saudação).
3. **Recuperação de Catálogo (`rag_retrieve`)**: Se a intenção demandar produtos, aciona o Vector Database (Redisearch) para buscar os top-K itens relevantes e cruza com dados frescos do banco relacional (PostgreSQL).
4. **Gerador de Resposta (`generate`)**: Monta o prompt final (instruções do sistema + produtos + histórico) e chama o LLM principal.
5. **Classificador de Estágio (`classify_stage`)**: Deduz qual é a etapa atual do funil de vendas (Greeting, Browsing, Ordering, Checkout) para mover o Kanban do CRM automaticamente.
6. **Extrator de Nome (`extract_name`)**: Tenta extrair o nome do cliente a partir do texto caso ainda não esteja salvo no banco de dados.

## 2. Abordagem de Fallback e Resiliência (LLMs)

O sistema suporta provedores duplos: **OpenAI** (GPT-4o / GPT-4o-mini) e **Google Gemini** (Gemini 1.5 Pro / Flash).
A inicialização do modelo (`llm.py`) tira proveito da função `.with_fallbacks()` do LangChain. Se o provedor principal (OpenAI) apresentar instabilidade, rate-limit ou indisponibilidade, o sistema roteia a requisição de forma transparente para o provedor secundário (Google Gemini), garantindo que o lojista nunca perca um atendimento.

## 3. Otimizações Extremas de Tokens (Economia)

Para garantir que o custo não escale exponencialmente em conversas longas, quatro abordagens independentes foram aplicadas simultaneamente:

### A. Roteamento Condicional do Catálogo (Intent Routing)
O fluxo do LangGraph foi projetado para pular o nó de RAG se o usuário enviar saudações ou mensagens que não sejam sobre roupas.
- **Antes**: Um "Oi" resultava na injeção do aviso "Nenhum catálogo disponível" ocupando espaço no System Prompt em cada turno.
- **Depois**: O bloco de instrução de produtos é removido integralmente antes da injeção se a intenção for `direct`.
- **Economia**: Redução de dezenas a centenas de tokens em conversas e bate-papos curtos.

### B. Janela Deslizante Parametrizada (Sliding Window)
O histórico textual puro da conversa (`conversation_context`) não cresce infinitamente. Foi adicionado um limite rígido via arquivo `.env` (ex: `CHAT_MAX_HISTORY_MESSAGES=4`).
- **Antes**: No 10º turno de uma conversa, todas as mensagens desde o "Bom dia" eram enviadas literalmente (~2.500 tokens).
- **Depois**: No 10º turno, apenas as mensagens mais recentes (últimas 4) são enviadas puras.

### C. Sumarização Contínua em Background (Rolling Summary)
Para evitar que o robô esqueça os detalhes cruciais descartados pela Janela Deslizante, um nó de compactação avalia os excessos.
Sempre que o número de mensagens for superior à janela configurada, uma tarefa secundária aciona o LLM "Fast" para resumir os diálogos distantes.
- **Como funciona**: O modelo de custo baixíssimo transforma mensagens originais (*"Vou querer levar a vermelha no tamanho M para minha sobrinha"* -> *"Cliente separou blusa vermelha M para a sobrinha"*) e adiciona ao JSON da tabela `conversations`.
- **Exemplo Prático**:
  - **Sem sumário**: Enviar o histórico inteiro de 30 turnos gasta ~10.000 tokens e estoura rapidamente o limite financeiro.
  - **Com sumário**: O sumário estabiliza em poucas sentenças e ocupa no máximo ~50 a 80 tokens, repassando o "conhecimento" essencial para a máquina a um custo marginal.

### D. Enxugamento e Compressão do RAG
O texto indexado e as descrições oriundas do banco não poluem o LLM ininterruptamente:
- Reduzimos o parâmetro padrão `RAG_TOP_K` de 5 para 3 (focando só na ultra-relevância).
- Truncamos no ato qualquer linha do banco com mais de 80 caracteres que não seja essencial (removendo descrições literárias desnecessárias e mantendo Tamanhos/Preço/Estoque).
- **Exemplo**:
  - Original: `Produto: Saia Longa \n Detalhes: Uma linda saia confeccionada nos alpes suíços por monges tecelões para o verão... \n Preço: R$ 89 \n Estoque: P` (~60 tokens).
  - Truncado: `Produto: Saia Longa \n Detalhes: Uma linda saia confec... \n Preço: R$ 89 \n Estoque: P` (~20 tokens).

## Conclusão e Teto de Consumo
Essas arquiteturas aliadas garantem que uma requisição média interativa estabilize-se virtualmente de forma horizontal (flat line) gastando em torno de **500 a 800 tokens**, independentemente do tamanho atual da conversa ou da escala do catálogo da loja, viabilizando o ModAI em um ecossistema SaaS de alta rotatividade.
