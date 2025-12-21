Perfeito. Vou criar um **relatório técnico**, organizado e claro, do jeito que você poderia:

* usar como **documento de decisão técnica**
* anexar a um **PR / revisão arquitetural**
* ou guardar como **rationale** do projeto

Sem código excessivo, focado em **o problema → risco → mudança sugerida → impacto**.

---

# 📄 Relatório Técnico

## Ajustes Críticos na Implementação do Grading Service (Streamlit ↔ ADK)

### Contexto

O módulo **Grading Service** atua como ponte entre a UI Streamlit (execução síncrona, baseada em reruns) e o backend ADK (execução assíncrona, orientada a eventos), incluindo suporte a *human-in-the-loop*.

Durante a análise da implementação atual, foram identificados **pontos críticos** que, embora não impeçam o funcionamento em MVP/demonstração, podem causar **instabilidade, comportamento imprevisível ou bugs intermitentes** em cenários reais ou de produção.

Este relatório descreve os **principais riscos** e as **mudanças recomendadas**.

---

## 1️⃣ Gerenciamento de Event Loop (`asyncio`)

### Situação atual

* O `asyncio event loop` é criado e armazenado em `st.session_state`.
* O mesmo loop é reutilizado entre múltiplos reruns do Streamlit.

### Problema identificado

* O Streamlit **não garante** que reruns ocorram no mesmo thread ou contexto.
* `asyncio event loop` é **amarrado ao thread** em que foi criado.
* Reutilizar loops entre reruns pode causar:

  * uso de loop fechado
  * loop associado a thread diferente
  * deadlocks silenciosos
  * vazamento de recursos (sockets, tasks pendentes)

### Risco

🔴 **Alto**, especialmente em:

* múltiplas execuções consecutivas
* ambientes com mais de um usuário
* deploys em cloud / containers

### Mudança sugerida

* Criar **um event loop por execução de grading**
* Fechar explicitamente o loop ao final da execução

### Impacto esperado

* Execução mais previsível
* Eliminação de loops “zumbis”
* Menor risco de travamentos intermitentes
* Melhor estabilidade para produção

---

## 2️⃣ Associação fraca entre Aprovação Humana e `invocation_id`

### Situação atual

* A decisão humana (`approval_decision`) é armazenada separadamente do `invocation_id`.
* A retomada do runner ocorre se **ambos existirem**, sem vínculo explícito.

### Problema identificado

* Possibilidade de **race condition**:

  * uma decisão pode ser aplicada ao `invocation_id` errado
  * principalmente em múltiplas execuções ou reruns rápidos

### Risco

🔴 **Alto**, pois pode:

* retomar execução incorreta
* aprovar/rejeitar ação errada
* gerar comportamento incoerente do pipeline

### Mudança sugerida

* Modelar a aprovação humana como **objeto estruturado**, contendo explicitamente:

  * `invocation_id`
  * decisão (`approved` / `rejected`)
  * timestamp
* Sempre aplicar a decisão **somente** ao invocation correspondente

### Impacto esperado

* Eliminação de race conditions
* Garantia de integridade do fluxo *human-in-the-loop*
* Base sólida para auditoria e logs futuros

---

## 3️⃣ Semântica indefinida para a ação “Reject”

### Situação atual

* A rejeição envia apenas um texto (`"User decision: rejected"`)
* O pipeline **continua a execução**
* O significado da rejeição fica implícito para o modelo

### Problema identificado

* “Reject” pode significar coisas diferentes:

  * abortar execução
  * negar execução de uma tool específica
  * pedir alternativa
* Delegar essa interpretação ao LLM é **arriscado**

### Risco

🔴 **Alto**, pois:

* o modelo pode ignorar a rejeição
* insistir na mesma ação
* executar ferramentas não desejadas
* gerar perda de controle do fluxo

### Mudança sugerida

* Definir semântica explícita para rejeição, por exemplo:

  * `abort_execution`
  * `deny_tool_and_continue`
* Representar isso de forma estruturada no estado da sessão

### Impacto esperado

* Workflow previsível
* Controle explícito de governança e guardrails
* Redução de comportamento inesperado do agente

---

## 4️⃣ Comunicação da decisão humana como texto livre

### Situação atual

* A decisão é enviada ao runner como texto simples:

  ```
  "User decision: approved"
  ```

### Problema identificado

* Texto livre é:

  * ambíguo
  * dependente da interpretação do modelo
  * frágil para evolução do sistema

### Risco

🟡 **Médio**, mas cresce com a complexidade do pipeline

### Mudança sugerida

* Enviar a decisão humana como **payload estruturado** (ex.: JSON),
  mesmo que encapsulado como texto:

  * evento
  * invocation_id
  * decisão
  * metadados

### Impacto esperado

* Comunicação mais robusta
* Facilidade de debugging
* Base para futuras integrações (logs, auditoria, replay)

---

## 📌 Prioridade de Correção (Ordem Recomendada)

1. **Definir semântica clara para Reject**
2. **Vincular aprovação humana ao `invocation_id`**
3. **Corrigir gerenciamento do event loop**
4. **Estruturar payload da decisão humana**

---

## ✅ Avaliação Final

* A **arquitetura geral é sólida** e demonstra bom entendimento de AgentOps e Human-in-the-Loop.
* Os problemas identificados **não invalidam o design**, mas afetam a **robustez operacional**.
* Com os ajustes propostos, o sistema evolui de:

  * **MVP funcional**
  * para **base confiável e escalável para produção**

---

Se quiser, no próximo passo posso:

* transformar este relatório em **checklist de PR**
* gerar uma **versão refatorada do código**
* ou criar um **diagrama de estados do pipeline** (RUNNING → WAITING_APPROVAL → RESUMED → DONE)

É só dizer como você pretende usar esse material.

---

## 5️⃣ Persistência de Sessão e Concorrência (Implementação Atual vs Ideal)

### Situação Resolvida (Workaround Estável)

Para corrigir os erros de concorrência (`TaskGroup IndexError`) causados pelo driver SQLite síncrono do ADK e a perda de sessão nos reruns do Streamlit, a seguinte implementação foi adotada:

1.  **InMemorySessionService**:
    *   Eliminamos o uso de SQLite temporariamente. O driver padrão do SQLite causava *race conditions* e travamentos quando múltiplos agentes paralelos tentavam persistir estado simultaneamente.
    *   Uso de memória evita latência de I/O e *locks* de banco.

2.  **Persistência no `st.session_state`**:
    *   O objeto `runner` (que contém o `InMemorySessionService` com os dados da sessão) agora é instanciado uma única vez e armazenado em `st.session_state._adk_runner`.
    *   A função `get_runner()` em `ui/services/grading.py` recupera essa instância singleton.
    *   Isso garante que, quando o Streamlit faz um *rerun* (ex: ao clicar em "Aprovar"), o backend ADK ainda possui o estado da execução anterior em memória, permitindo o `resume` correto.

### Caminho para Escalabilidade (Produção)

A solução atual é ideal para desenvolvimento e demos, mas possui limitações claras de escalabilidade. Para um ambiente de produção multiusuário, recomenda-se:

1.  **Banco de Dados Robusto (PostgreSQL)**:
    *   Substituir `InMemorySessionService` por `DatabaseSessionService` conectado a um PostgreSQL.
    *   O Postgres gerencia nativamente concorrência de transações, resolvendo o problema de *TaskGroup* sem perder a persistência real.

2.  **SQLite Assíncrono (Caso intermediário)**:
    *   Se PostgreSQL não for viável, configurar o ADK para usar um driver puramente assíncrono para SQLite (ex: `sqlite+aiosqlite://`).
    *   Ativar modo WAL (`PRAGMA journal_mode=WAL`) para melhorar concorrência de escrita.

3.  **Localização do `get_runner`**:
    *   **Atual**: A função `get_runner` reside em `ui/services/grading.py`. Isso acopla a lógica de UI com a construção do backend.
    *   **Melhoria**: Mover a lógica de instanciação e cache do runner para um módulo dedicado de injeção de dependência (ex: `app/container.py` ou `agent_factory.py`). A UI deveria apenas consumir o serviço pronto, sem saber se ele está no `session_state` ou vindo de um pool.
