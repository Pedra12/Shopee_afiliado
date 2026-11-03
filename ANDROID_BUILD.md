# Aplicativo Android

Este módulo gera um APK Android que incorpora o painel Python existente com Chaquopy, sem exigir Termux no aparelho.

## O que está implementado

- Aplicativo Android nativo com WebView local.
- O painel e o backend rodam dentro do processo do aplicativo, em localhost.
- Credenciais da API são informadas no primeiro uso e ficam no armazenamento privado do aplicativo.
- Perfil oficial de integração e painel HTML são empacotados no APK.
- A página de produto Shopee pode ser aberta dentro do WebView.
- A ação manual **Detectar vídeo** procura URLs MP4 expostas pela própria página e oferece os resultados para download pelo Android DownloadManager.
- O download é manual e o app não publica, não curte, não segue nem automatiza ações da conta.

## Compilação

O workflow `.github/workflows/android-apk.yml` compila o APK de depuração em GitHub Actions e publica o arquivo como artefato `shopee-afiliado-debug-apk`.

O primeiro build também valida se as dependências Python usadas pelo backend são compatíveis com Chaquopy/Android. Se algum pacote não tiver wheel Android compatível, o workflow falhará e a dependência deverá ser substituída ou portada antes de distribuir o APK.

## Limites da extração

O botão detecta somente vídeos cujo endereço MP4 esteja acessível no HTML/DOM da página aberta. A Shopee pode mudar a estrutura, exigir sessão ou não expor o arquivo direto. O app não remove marcas d'água incorporadas ao vídeo, não contorna DRM e não promete que todo anúncio terá um MP4 baixável. Use apenas vídeos próprios ou com autorização de reutilização.
