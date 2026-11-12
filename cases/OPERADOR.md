# OPERADOR — Como rodar um caso da Fase B

Para quem conduz a execução (humano ou script). O agente de IA lê só `cases/AGENT.md` e `cases/C<n>.md`. Todos os comandos rodam na raiz do repositório.

## Uma vez por sessão

1. Confira que nada mais usa o ambiente: nem `harness run` (Fase A) nem outro agente. O ambiente e o teclado do display isolado são compartilhados.
2. `app/build.sh` se `bin/cadcli` não existir.
3. Suba o ambiente:

   ```bash
   python3 -m harness env up      # imprime window_id, display ":2" e terminal
   ```

## Antes de cada repetição

O `harness` não tem comando de reinício do app. O equivalente ao `restart_app` do `harness/launcher.py` é o `respawn-pane` abaixo.

```bash
app/reset.sh                                            # dados de volta ao seed
if tmux -L cadcli has-session -t cadcli 2>/dev/null; then
  tmux -L cadcli respawn-pane -k -t cadcli "$PWD/app/run.sh"    # reinicia só o app
else
  python3 -m harness env down && python3 -m harness env up      # depois do C2 o app saiu e a janela fechou
fi
tmux -L cadcli capture-pane -p -t cadcli | head -1      # repita até a linha terminar em T01
```

O agente acha o window-id sozinho. Ele pode mudar depois de `env down`/`env up`; não precisa passar ao agente.

## Rodar o caso

1. Escolha um `run_id` novo, por exemplo `B-C3-r1-$(date +%Y%m%d-%H%M%S)`. Não reutilize.
2. Abra uma sessão **nova** do agente para cada repetição, sem histórico de execuções anteriores.
3. Entregue ao agente, por exemplo:

   > Leia `cases/AGENT.md` e `cases/C3.md` e execute o caso C3. run_id: `B-C3-r1-20261112-150000`. Raiz do repositório: `/opt/projetos/poc-agent-desktop-test-automation`.

4. Aprove os comandos do agente conforme pedidos. Não use modo que pula permissões. Recuse qualquer comando fora do que o `cases/AGENT.md` permite (por exemplo `tmux`, `agent-desktop` direto, leitura de `data/` ou `tests/`) e registre a tentativa.
   - Se o agente rodar como subagente, sem aprovação manual de comandos, registre isso no resultado da repetição (o `agent-result.json` traz `"aprovacao_manual": false`; anote também junto ao `verify.json`).
5. Não mexa no teclado nem no mouse dentro da janela `CADCLI-DISPLAY` durante a execução.

## Julgar

Logo depois que o agente terminar, **antes** do próximo `app/reset.sh` (o `verify` lê o estado atual):

```bash
python3 -m harness verify C3 --result evidence/<run_id>/agent-result.json | tee evidence/<run_id>/verify.json
```

- Sai 0 se passou, 1 se não. `state` é o oráculo (tela tmux e `data/clientes.dat`); `claims` compara o que o agente declarou.
- Sem `agent-result.json`, ou com `abortado`: a repetição conta como falha.
- No C2 o `verify` espera a sessão tmux encerrada. Rode-o antes de subir o ambiente de novo.

## Registrar

São 3 repetições por caso (critério do PRD: pelo menos 2 de 3). Para cada uma, guarde em `evidence/<run_id>/`: `agent-result.json`, `verify.json` e, se a ferramenta de IA mostrar, o custo da sessão (tokens). Anote também comandos recusados no passo 4. `evidence/` não vai para o git.

Ao terminar a sessão: `python3 -m harness env down`.
