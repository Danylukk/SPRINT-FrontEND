# Sprint 3 - Motor Digital Twin | Inteligência Operacional

<<<<<<< HEAD
Projeto acadêmico em Streamlit para cadastro técnico e acompanhamento operacional simulado de motores. A Sprint 2 evolui a base da Sprint 1 sem refazê-la: mantém `data/equipments.json`, cadastro, consulta, ficha técnica e Dados Brutos, e adiciona um **Dashboard Operacional** com histórico local, alertas e gráficos temporais.
=======
Projeto acadêmico em **Streamlit** que evolui diretamente as Sprints 1 e 2 do Motor Digital Twin. A Sprint 3 adiciona a camada visual de **alertas, estados operacionais, histórico de eventos, resumos textuais e apoio inicial à decisão**, preservando cadastro técnico, consulta, dados brutos, telemetria simulada, histórico temporal e Dashboard Operacional já existentes.

## Objetivo da Sprint 3
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)

Criar uma página inicial, antes da seleção de equipamentos, capaz de apresentar de forma clara e proativa:

<<<<<<< HEAD
- Dashboard geral dos ativos cadastrados.
- Cadastro técnico com validação de campos obrigatórios e bloqueio de TAG duplicada.
- Consulta de equipamentos e ficha técnica individual.
- Dados Brutos simulados, mantendo a camada antiga sem MQTT real.
- Dashboard Operacional por área/planta usando `local_instalacao`.
- Seleção de TAG filtrada pela área.
- Telemetria atual simulada por temperatura, vibração, corrente e rotação.
- Histórico em `data/telemetry_history.csv`.
- Gráficos interativos com Plotly.
- Alertas visuais por severidade.
- Placa simulada do motor com placeholder visual em HTML/CSS e card técnico dinâmico.
=======
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
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)

## Tecnologias

- Python
- Streamlit
- Pandas
- Plotly
<<<<<<< HEAD
- JSON para cadastro técnico local
- CSV para histórico de telemetria local
=======
- JSON para cadastro técnico
- CSV para históricos locais
- `unittest` para validação automatizada
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)

## Como executar

```bash
python -m venv .venv
<<<<<<< HEAD
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

No Linux/macOS, ative o ambiente com:
=======
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)

```bash
source .venv/bin/activate
```

<<<<<<< HEAD
Depois de iniciar, acesse o endereço exibido pelo Streamlit, normalmente:
=======
Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute:

```bash
streamlit run app.py
```

## Testes
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)

Execute a suíte automatizada:

```bash
python -m unittest discover -s tests -v
```

<<<<<<< HEAD
## Estrutura do projeto

```text
sprint1_motor_digital_twin/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── equipments.json
│   └── telemetry_history.csv
└── src/
    ├── models/
    │   └── equipment.py
    ├── repositories/
    │   ├── equipment_repository.py
    │   └── telemetry_repository.py
    ├── services/
    │   ├── alert_service.py
    │   ├── equipment_service.py
    │   ├── sensor_service.py
    │   └── telemetry_service.py
    └── ui/
        ├── components.py
        └── pages.py
```
=======
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
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)

## Sprints anteriores preservadas

<<<<<<< HEAD
Os equipamentos continuam persistidos em `data/equipments.json`. A Sprint 2 adiciona exemplos para áreas operacionais úteis:

- Linha de Produção A
- Linha de Produção B
- Utilidades
- Bombeamento

O histórico operacional é criado automaticamente em `data/telemetry_history.csv` com as colunas:

```text
timestamp, tag, temperatura_c, vibracao_mm_s, corrente_a, rotacao_rpm
```

Quando uma TAG ainda não tem histórico, o app gera pontos simulados iniciais. O botão **Gerar nova leitura simulada** acrescenta uma nova linha ao CSV para a TAG selecionada.
=======
A navegação continua disponibilizando:

- Dashboard Operacional;
- Cadastro Técnico;
- Consulta de Equipamentos;
- Dados Brutos;
- Sobre o Projeto.

A Sprint 3 adiciona a nova Home sem eliminar os fluxos construídos anteriormente.

## Roteiro recomendado para o vídeo
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)

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

<<<<<<< HEAD
- Temperatura: até 70 °C é saudável; até 85 °C é atenção; acima de 85 °C é crítico.
- Vibração: até 4,5 mm/s é saudável; até 7,0 mm/s é atenção; acima de 7,0 mm/s é crítico.
- Corrente: até 100% da corrente nominal é saudável; até 115% é atenção; acima de 115% é crítico.

A saúde geral do ativo é calculada pelo pior status entre temperatura, vibração e corrente.

## Placa simulada

A Sprint 2 exibe uma placa simulada do motor na seção **Placa do Motor** do Dashboard Operacional. Ela é um placeholder visual em HTML/CSS com aparência de placa industrial, exibindo TAG, modelo, fabricante, potência, tensão, corrente nominal e rotação nominal a partir do cadastro do ativo.

Essa placa representa visualmente a identificação do motor selecionado e reforça a rastreabilidade entre cadastro, localização e telemetria. O card técnico permanece abaixo da placa para deixar os dados legíveis e vinculados ao cadastro.

OCR e visão computacional real não foram implementados nesta Sprint. A interface apenas prepara o espaço visual para uma evolução futura com leitura real de imagens de placa.
=======
## Observação final

Os alertas e recomendações desta Sprint são recursos acadêmicos de apoio inicial e não substituem inspeção ou decisão técnica de uma equipe de manutenção.
>>>>>>> 4b32ae8 (feat: implementa inteligencia operacional da Sprint 3)
