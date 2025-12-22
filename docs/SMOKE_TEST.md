# Smoke Test Manual - Provider Switching

Este guia descreve como testar manualmente o sistema de troca de provider LLM.

## Pré-requisitos

1. **API Keys configuradas:**
   ```bash
   export GEMINI_API_KEY="sua-chave-gemini"
   export OPENAI_API_KEY="sua-chave-openai"
   ```

2. **Iniciar aplicação:**
   ```bash
   streamlit run ui/app.py
   ```

## Teste 1: Troca de Provider Básica

### Objetivo
Validar que a troca de provider recria o runner/app corretamente.

### Passos

1. **Iniciar com Gemini (default)**
   - Abrir a aplicação
   - Verificar no sidebar: "LLM Provider: Gemini" está selecionado
   - Verificar nos logs do terminal: `✅ Runner configured with InMemorySessionService`

2. **Criar rubric e submission**
   - Colar um rubric JSON válido
   - Colar uma submission de teste
   - Clicar em "Start Grading"

3. **Observar execução com Gemini**
   - Verificar que o grading inicia
   - Aguardar conclusão
   - Verificar resultado final

4. **Trocar para OpenAI**
   - No sidebar, selecionar "OpenAI" no dropdown
   - Verificar que a UI recarrega (st.rerun)
   - Verificar nos logs: novo runner sendo criado

5. **Repetir grading com OpenAI**
   - Usar mesmo rubric/submission
   - Clicar em "Start Grading"
   - Verificar que funciona com OpenAI

### Resultado Esperado
- ✅ Troca de provider não causa erros
- ✅ Cada provider usa seu próprio modelo
- ✅ Resultados são independentes (não há "vazamento" de estado)

---

## Teste 2: Aprovação HITL com Troca de Provider

### Objetivo
Validar que trocar provider durante/antes de approval limpa o estado corretamente.

### Passos

1. **Configurar rubric que force approval**
   - Usar rubric com critério que resulte em score < 50% ou > 90%
   - Ou usar env var `FORCE_APPROVAL=true` (se implementado)

2. **Iniciar grading com Gemini**
   - Clicar em "Start Grading"
   - Aguardar até aparecer "⚠️ Approval Required"
   - **NÃO CLICAR** em Approve/Reject ainda

3. **Trocar para OpenAI enquanto approval está pendente**
   - No sidebar, trocar para "OpenAI"
   - Verificar que a UI recarrega

4. **Verificar estado limpo**
   - Verificar que não há mais mensagem de approval pendente
   - Verificar que pode iniciar novo grading sem problemas

5. **Testar approval normal (sem trocar provider)**
   - Iniciar novo grading com OpenAI
   - Aguardar approval
   - Clicar em "Approve" ou "Reject"
   - Verificar que o fluxo continua corretamente

### Resultado Esperado
- ✅ Trocar provider limpa `pending_approval`, `approval_decision`, `last_invocation_id`
- ✅ Não tenta fazer "resume" com runner diferente
- ✅ Approval funciona normalmente quando não há troca de provider

---

## Teste 3: Cache de Runner por Provider

### Objetivo
Validar que o runner é cacheado por provider e reutilizado.

### Passos

1. **Primeira execução com Gemini**
   - Selecionar Gemini
   - Executar grading
   - Observar logs: `✅ Runner configured...`

2. **Segunda execução com Gemini (sem trocar)**
   - Executar outro grading
   - Verificar que **não** aparece novo log de criação de runner
   - Runner deve ser reutilizado do cache

3. **Trocar para OpenAI**
   - Selecionar OpenAI
   - Observar logs: novo runner sendo criado

4. **Voltar para Gemini**
   - Selecionar Gemini novamente
   - Observar logs: novo runner sendo criado (cache foi invalidado)

### Resultado Esperado
- ✅ Runner é reutilizado quando provider não muda
- ✅ Runner é recriado quando provider muda
- ✅ Cada provider tem seu próprio cache

---

## Teste 4: Event Loop Cleanup

### Objetivo
Validar que o event loop não persiste e é limpo corretamente.

### Passos

1. **Executar múltiplos gradings**
   - Executar 3-5 gradings consecutivos
   - Alternar entre providers

2. **Verificar logs de warnings**
   - Não deve aparecer: `RuntimeWarning: coroutine was never awaited`
   - Não deve aparecer: `ResourceWarning: unclosed event loop`

3. **Verificar memória (opcional)**
   - Usar `htop` ou Activity Monitor
   - Verificar que memória não cresce indefinidamente

### Resultado Esperado
- ✅ Sem warnings de event loop
- ✅ Memória estável
- ✅ Sem vazamento de recursos

---

## Checklist Final

Após executar todos os testes:

- [ ] Troca de provider funciona sem erros
- [ ] Approval state é limpo ao trocar provider
- [ ] Runner é cacheado por provider
- [ ] Event loop é limpo corretamente
- [ ] Sem warnings no terminal
- [ ] UI responsiva e sem travamentos

---

## Troubleshooting

### Erro: "API key not valid"
- Verificar que as API keys estão configuradas corretamente
- Verificar que a key corresponde ao provider selecionado

### Erro: "ADK backend not available"
- Verificar que o `agent.py` foi carregado sem erros
- Verificar logs de inicialização

### UI não atualiza ao trocar provider
- Verificar que `st.rerun()` está sendo chamado em `ui/components/sidebar.py`
- Verificar que `invalidate_runner()` está sendo chamado

### Approval não funciona
- Verificar que `last_invocation_id` está sendo capturado
- Verificar que `resume_runner_with_confirmation` está sendo chamado
- Verificar logs do ADK para mensagens de erro
