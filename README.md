# Shopee Afiliado

Painel mobile independente para garimpar produtos, consultar ofertas da Shopee Brasil e acompanhar sinais de procura.

## O que já está integrado

- Backend Shopee Affiliate Open API incorporado em `vendor/shopee-br-affiliate-mcp/`, preservando o código original, os créditos e a licença MIT.
- Garimpo automático em oito categorias, com deduplicação e ordenação por vendas.\n- Pesquisa de produtos com ordenação por vendas, preço e comissão, conforme os campos liberados para a conta.
- Geração oficial de links de afiliado.
- Histórico local de observações para comparar vendas, apenas quando a API fornece períodos comparáveis.
- Sinais de tendência do Google Trends Brasil via `trendspyg` (RSS), com cache.
- Painel responsivo em português para celular.
- Testes automatizados upstream e testes de integração do painel no GitHub Actions.

## Limites que precisam ficar claros

- O backend upstream declara que seus testes de API são simulados. A conexão live ainda precisa ser validada com as credenciais e permissões reais da conta.
- Google Trends fornece índice/sinal relativo, não vendas nem volume real de buscas na Shopee. A fonte RSS não é uma API oficial de integração e pode sofrer limitação temporária.
- A API oficial de afiliados não fornece o arquivo de vídeo do anúncio. Os termos da Shopee proíbem scraping automatizado e reutilização de conteúdo de terceiros sem autorização. Por isso, o painel não extrai nem baixa vídeos de anúncios de outros criadores. Vídeos próprios ou autorizados podem ser tratados separadamente.
- O histórico de vendas começa quando o painel passa a registrar observações; não recupera vendas históricas anteriores.

## Instalação no Android (Termux)

1. Instale Termux e atualize os pacotes:
   ```sh
   pkg update && pkg upgrade
   pkg install python git
   ```
2. Baixe o repositório e entre na pasta:
   ```sh
   git clone https://github.com/Pedra12/Shopee_afiliado.git
   cd Shopee_afiliado
   ```
3. Crie o ambiente e instale as dependências:
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Crie seu arquivo local de configuração:
   ```sh
   cp .env.example .env
   nano .env
   ```
5. Preencha somente no arquivo local `.env`:
   - `SHOPEE_APP_ID`: seu App ID
   - `SHOPEE_APP_SECRET`: seu App Secret
   - `SHOPEE_ACCOUNT_REFERENCE`: rótulo local para identificar a conta
   - Deixe `SHOPEE_MODE=` vazio para o app selecionar live quando encontrar as duas credenciais.
6. Inicie:
   ```sh
   python app.py
   ```
7. Abra no navegador do próprio celular: `http://127.0.0.1:5000`.

## Segurança

- Nunca envie App ID, App Secret ou tokens em mensagens.
- Nunca faça commit do arquivo `.env`; ele já está no `.gitignore`.
- Não coloque credenciais em arquivos do GitHub.
- A primeira pesquisa em modo live será o teste real da API. Se a Shopee recusar a assinatura, o escopo ou a conta, o painel mostrará a falha sem expor os segredos.

## Fonte Shopee incorporada

- [jeffmonteiroo/shopee-br-affiliate-mcp](https://github.com/jeffmonteiroo/shopee-br-affiliate-mcp)
- Versão indicada pelo upstream: 0.5.0
- Licença MIT preservada em `vendor/shopee-br-affiliate-mcp/LICENSE`.
- Registro de origem e commit: `vendor/shopee-br-affiliate-mcp/UPSTREAM.txt`.

## Fonte de tendências

- [flack0x/trendspyg](https://github.com/flack0x/trendspyg)
- Dependência fixada em `requirements.txt` na versão 1.9.0, licença MIT.
- A integração usa somente a rota RSS sem navegador; a análise Explore mais profunda não é usada no painel para evitar dependência de Chrome e chamadas sensíveis a limites.

Este projeto é independente de todos os outros repositórios do proprietário e não é afiliado, endossado ou suportado oficialmente pela Shopee ou pelo Google.
