# Roteiro de avaliação — CP6

1. Inicie API e front nos dois terminais do README. Confirme `provider=simulated` em `/health` e abra `/docs`.
2. No front, crie uma conta local e entre. A conta começa sem conversas.
3. Clique em **Nova conversa**, envie “O que é uma API?” e confira a mensagem e a resposta simulada.
4. Envie outra mensagem na mesma conversa. O bot informa o número da interação a partir do histórico persistido.
5. Crie outra conversa e envie “Como o histórico é persistido?”. Alterne as duas pela barra lateral e confira que os históricos são independentes.
6. Interrompa apenas o backend com `Ctrl+C` e inicie novamente com o mesmo `.env` e `DATABASE_PATH`. Clique em **Atualizar histórico** no front: as mensagens permanecem.
7. Clique em **Sair**. Crie e entre com outra conta: nenhuma conversa da primeira aparece. Entre novamente com a primeira para retomar o histórico.
8. Em `/docs`, chame uma rota protegida sem token: **401**. Faça login, copie `access_token` e use **Authorize**. Crie, liste e retome conversas pela API.
9. Envie mensagem vazia: **422**. Consulte ID inexistente ou pertencente à outra conta: **404**.
10. Defina `LLM_PROVIDER=unavailable` no `.env` do backend e reinicie. O envio mostra erro amigável **503**, sem interação incompleta. Restaure `simulated` ao terminar.
11. Desligue a API e tente atualizar o histórico. A UI mostra o problema sem traceback. Inicie a API novamente.

O vídeo `video-cp6.mp4` é uma gravação local com legendas, sem áudio. As contas são fictícias e o banco demonstrativo não é versionado. A gravação é apoio para a avaliação; código e instalação são a entrega principal.
