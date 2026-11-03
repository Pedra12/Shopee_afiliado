# Shopee Afiliado

Projeto independente para centralizar descoberta de produtos, análise de oportunidades e organização de materiais de afiliados Shopee Brasil.

## Estado atual

- Backend de integração com a Shopee Affiliate Open API incorporado em `vendor/shopee-br-affiliate-mcp/`.
- Código upstream mantido com sua licença MIT e aviso de copyright.
- Testes automatizados upstream preservados em `vendor/shopee-br-affiliate-mcp/tests/`.
- Workflow do GitHub Actions configurado para executar os testes em Python 3.11 e 3.12.
- O painel web unificado e o mecanismo de descoberta de tendências ainda serão integrados.

## Fonte incorporada

- Projeto: [jeffmonteiroo/shopee-br-affiliate-mcp](https://github.com/jeffmonteiroo/shopee-br-affiliate-mcp)
- Versão indicada pelo upstream: 0.5.0
- Licença: MIT. Consulte `vendor/shopee-br-affiliate-mcp/LICENSE`.
- O backend disponibiliza pesquisa de ofertas, ordenação por vendas, consulta de produtos, ofertas de lojas/campanhas, feeds, geração de links e relatórios, conforme o acesso liberado à conta.
- O próprio autor informa que os testes de integração foram simulados e que a aceitação real depende das permissões e do contrato ativo da conta Shopee.

## Segurança

- Nunca publique App ID, App Secret, tokens ou relatórios privados.
- Não coloque credenciais em arquivos versionados nem as envie em conversas.
- O backend lê as credenciais de variáveis de ambiente locais.
- O modo `fixture` usa dados sintéticos. Ele não comprova conexão real.
- O uso em modo `live` só deve ser habilitado após validar o acesso real da conta e o perfil oficial da API.

## Execução do backend incorporado

Consulte as instruções preservadas em `vendor/shopee-br-affiliate-mcp/README.md` e `vendor/shopee-br-affiliate-mcp/docs/LOCAL-TEST.md`.

## Próxima integração

O painel principal deverá chamar o backend incorporado, apresentar resultados em português e guardar histórico local para identificar evolução de vendas. Sinais externos de tendência serão rotulados como estimativas, separados dos dados de vendas fornecidos pela Shopee.

Este repositório não é afiliado, endossado ou suportado oficialmente pela Shopee.
