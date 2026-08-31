# Sprint 3 — Motor Digital Twin

Projeto acadêmico em Streamlit que mantém as entregas das Sprints 1 e 2 e acrescenta um painel de inteligência operacional para alertas, estados, histórico e apoio inicial à decisão.

## O que a Sprint 3 demonstra

- Estado analítico único por equipamento, exposto à UI por `OperationalSnapshot`.
- Atualização DEMO determinística do `MTR-001`: `Saudável → Crítico → Saudável`.
- Nova leitura local com timestamp, origem e `reading_id` a cada atualização.
- Nova inferência com `inference_id`, provider e `score=None` (sem score fictício).
- Eventos apenas para transições reais, sem duplicação em reruns.
- Indicação neutra para dados indisponíveis ou desatualizados.
- Histórico seed versionado separado do histórico runtime ignorado pelo Git.

## Transparência acadêmica

Não há Machine Learning, API externa ou NLP real nesta entrega.

- `RulesAnalyticsProvider` classifica as leituras com os thresholds já existentes.
- `NLPSummaryService` usa templates determinísticos e se identifica como `mock_nlp`.
- Um futuro `MLAnalyticsProvider` pode implementar o mesmo contrato `AnalyticsProvider`; a UI continuará consumindo apenas o resultado analítico.

## Arquitetura

```text
Telemetria (seed, simulação ou DEMO)
        ↓
AnalyticsProvider (RulesAnalyticsProvider hoje)
        ↓
OperationalSnapshot
        ↓
Session state analítico
        ↓
UI Streamlit → Event history runtime
```

O cadastro técnico (`Operacional`, `Inativo` etc.) continua separado do estado analítico (`Saudável`, `Atenção`, `Crítico`, `Indisponível`).

## Dados locais

`data/telemetry_history.csv` e `data/event_history.csv` são referências versionadas e nunca recebem a escrita de uma demonstração. Novas leituras e eventos são gravados em `data/runtime/`, que está no `.gitignore`.

Uma leitura com mais de 120 minutos recebe o indicador neutro “Dados desatualizados”; idade do dado não é uma anomalia. Valores ausentes, inválidos ou não finitos são “Indisponível”, nunca críticos automaticamente.

## Roteiro DEMO

1. Abra **Painel de Alertas e Estados** e localize `MTR-001` saudável.
2. Clique em **Atualizar informações**.
3. Uma leitura DEMO atual com vibração de `7,80 mm/s` é criada e analisada.
4. O painel, o card, o resumo `mock_nlp`, a recomendação e o histórico passam a mostrar **Crítico** com a mesma origem e timestamp.
5. O evento `Saudável → Crítico` é gravado uma única vez.
6. Clique novamente para demonstrar a recuperação `Crítico → Saudável`.

## Sprints anteriores

Dashboard Operacional, Cadastro Técnico, Consulta de Equipamentos, Dados Brutos, filtros por área/TAG, gráficos, ficha técnica, placa simulada e geração de telemetria continuam disponíveis.

## Como executar

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Testes

```bash
python -m unittest discover -s tests -v
python -m pytest -q
python -m compileall -q app.py src tests
python -m pip check
```

Os testes cobrem thresholds preservados, baseline e desvio DEMO, transições, rerun, recuperação, timestamp, IDs, `mock_nlp`, estado administrativo independente, `NaN`, separação seed/runtime e erros controlados de JSON/CSV.
