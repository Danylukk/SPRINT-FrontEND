# Sprint 3 - Motor Digital Twin | Inteligência Operacional

Projeto acadêmico em **Streamlit** que evolui diretamente as Sprints 1 e 2 do Motor Digital Twin. A Sprint 3 adiciona a camada visual de **alertas, estados operacionais, histórico de eventos, resumos textuais e apoio inicial à decisão**, preservando cadastro técnico, consulta, dados brutos, telemetria simulada, histórico temporal e Dashboard Operacional já existentes.

## Objetivo da Sprint 3

Criar uma página inicial, antes da seleção de equipamentos, capaz de apresentar de forma clara e proativa:

- estado consolidado dos ativos;
- alertas prioritários;
- mudança dinâmica entre **Saudável**, **Atenção** e **Crítico**;
- resumo textual do alerta;
- recomendação inicial para manutenção;
- histórico de mudanças de estado;
- atualização manual do painel com cenário controlado de anomalia.

## Transparência acadêmica

Esta entrega **não afirma possuir Machine Learning ou NLP real quando eles não estão integrados**.

- A classificação operacional utiliza o `AlertService` da Sprint 2 como **fallback analítico por regras**.
- O botão **Atualizar informações** alterna um cenário controlado no ativo `MTR-001`, permitindo demonstrar a transição de um estado normal para um estado crítico.
- Os resumos textuais são gerados por `NLPSummaryService` com templates determinísticos (**mock NLP**).
- O Front-End consome o resultado por meio de `OperationalIntelligenceService`, mantendo a interface desacoplada da origem analítica. Um modelo de ML/NLP real pode substituir essa origem futuramente sem reescrever a página.

## Funcionalidades da Sprint 3

### Painel de Alertas e Estados

Nova página inicial com:

- KPIs de ativos monitorados, saudáveis, em atenção e críticos;
- alertas prioritários ordenados por severidade;
- resumo inteligente de cada alerta;
- apoio inicial à decisão;
- tabela consolidada com estado, área, temperatura, vibração e corrente;
- histórico persistente de mudanças de estado em `data/event_history.csv`;
- botão de atualização das informações;
- mensagem visual quando um novo estado é detectado.

### Demonstração da transição de estado

1. Abra o **Painel de Alertas e Estados**.
2. Observe o `MTR-001` em seu baseline operacional.
3. Clique em **Atualizar informações**.
4. O cenário controlado altera a vibração para `7,80 mm/s`.
5. As regras existentes classificam o ativo como **Crítico**.
6. A interface exibe o novo alerta, o resumo textual e a recomendação.
7. A mudança é registrada no histórico de eventos.
8. Clique novamente em **Atualizar informações** para retornar ao cenário base e registrar a nova transição.

## Arquitetura

```text
src/
├── models/
│   ├── equipment.py
│   └── operational_event.py              # novo: contrato do histórico de eventos
├── repositories/
│   ├── equipment_repository.py
│   ├── telemetry_repository.py
│   └── event_repository.py               # novo: persistência do histórico
├── services/
│   ├── alert_service.py                   # preservado da Sprint 2
│   ├── equipment_service.py
│   ├── sensor_service.py
│   ├── telemetry_service.py
│   ├── nlp_summary_service.py             # novo: adapter mock NLP
│   └── operational_intelligence_service.py# novo: contrato analítico desacoplado
└── ui/
    ├── components.py                      # preservado
    ├── pages.py                           # preservado
    ├── sprint3_components.py              # novo: componentes reutilizáveis
    └── sprint3_pages.py                   # novo: navegação + painel Sprint 3

data/
├── equipments.json
├── telemetry_history.csv
└── event_history.csv                      # novo

tests/
└── test_sprint3.py
```

### Fluxo desacoplado

```text
Telemetria / futuro ML
        ↓
OperationalIntelligenceService
        ↓
OperationalSnapshot
        ↓
Front-End Streamlit

NLP real futuro
        ↓
NLPSummaryService (mesmo contrato)
        ↓
Resumo + recomendação
```

## Regras preservadas da Sprint 2

- Temperatura: até 70 °C saudável; até 85 °C atenção; acima de 85 °C crítico.
- Vibração: até 4,5 mm/s saudável; até 7,0 mm/s atenção; acima de 7,0 mm/s crítico.
- Corrente: até 100% da corrente nominal saudável; até 115% atenção; acima de 115% crítico.
- A saúde geral continua sendo definida pelo pior status encontrado.

## Tecnologias

- Python
- Streamlit
- Pandas
- Plotly
- JSON para cadastro técnico
- CSV para históricos locais
- `unittest` para validação automatizada

## Como executar

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
streamlit run app.py
```

## Testes

Execute a suíte automatizada:

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem:

- regressão dos thresholds da Sprint 2;
- baseline classificado como saudável;
- cenário simulado classificado como crítico;
- vibração como variável dominante no cenário de demonstração;
- geração do resumo mock NLP;
- recomendação de apoio inicial à decisão;
- preservação da leitura original sem mutação acidental;
- transição `Saudável → Crítico`;
- persistência e releitura do histórico de eventos.

## Sprints anteriores preservadas

A navegação continua disponibilizando:

- Dashboard Operacional;
- Cadastro Técnico;
- Consulta de Equipamentos;
- Dados Brutos;
- Sobre o Projeto.

A Sprint 3 adiciona a nova Home sem eliminar os fluxos construídos anteriormente.

## Roteiro recomendado para o vídeo

1. Abrir o sistema diretamente no **Painel de Alertas e Estados**.
2. Explicar os KPIs e os estados por cor.
3. Destacar que o Front está desacoplado dos modelos analíticos.
4. Mostrar o `MTR-001` no cenário base.
5. Clicar em **Atualizar informações**.
6. Mostrar a transição para **Crítico** e o novo alerta.
7. Ler rapidamente o **Resumo inteligente**.
8. Mostrar o card de **Apoio inicial à decisão**.
9. Mostrar o evento registrado no histórico.
10. Explicar que ML/NLP real podem substituir os adapters atuais sem alterar a interface.

## Observação final

Os alertas e recomendações desta Sprint são recursos acadêmicos de apoio inicial e não substituem inspeção ou decisão técnica de uma equipe de manutenção.
