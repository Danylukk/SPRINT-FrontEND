# Roteiro de avaliação — CP6

1. Inicie API e front nos dois terminais do README. Confirme `provider=simulated` em `/health` e abra `/docs`.
2. No front, crie uma conta e entre. O dashboard abre com todos os módulos no menu lateral. Acesse cadastro, consulta e dados brutos das sprints anteriores.
3. No **Painel de Alertas e Estados**, atualize a DEMO de MTR-001. Consulte a mesma TAG no **Dashboard Operacional** e confira leitura, origem e gráficos. Na **Consulta de Equipamentos**, abra **Conversar sobre MTR-001**: o chat usa o mesmo estado e ID da leitura.
4. No **Assistente IA**, clique em **Nova conversa**, envie “O que é uma API?” e confira a resposta simulada. Troque os módulos e retome as conversas pela barra lateral.
5. Crie outra conversa e envie “Como o histórico é persistido?”. Alterne as conversas pela barra lateral e confira que os históricos são independentes.
6. Interrompa apenas o backend com `Ctrl+C` e inicie novamente com o mesmo `.env` e `DATABASE_PATH`. Clique em **Atualizar histórico** no front: as mensagens permanecem.
7. Clique em **Sair**. Crie e entre com outra conta: os equipamentos são compartilhados, mas nenhuma conversa da primeira aparece. Entre novamente com a primeira para retomar o histórico.
8. Em `/docs`, chame uma rota protegida sem token: **401**. Faça login, copie `access_token` e use **Authorize**. Crie, liste e retome conversas pela API.
9. Envie mensagem vazia: **422**. Consulte ID inexistente ou pertencente à outra conta: **404**.
10. Defina `LLM_PROVIDER=unavailable` no `.env` do backend e reinicie. O envio mostra erro amigável **503**, sem interação incompleta. Restaure `simulated` ao terminar.
11. Desligue a API e tente atualizar o histórico. A UI mostra o problema sem traceback. Inicie a API novamente.

O vídeo `video-cp6.mp4` é uma gravação local com legendas, sem áudio. As contas são fictícias e o banco demonstrativo não é versionado. A gravação é apoio para a avaliação; código e instalação são a entrega principal.
