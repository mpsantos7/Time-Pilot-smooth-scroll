# Time Pilot — Smooth Scroll

Patch de scroll fino para Time Pilot (Konami, MSX1), baseado na versão v7 testada no projeto. A build transforma uma ROM original de 16 KB fornecida pelo usuário em uma ROM de 32 KB, com scroll de um pixel e tratamento dos 16 rumos.

Este repositório contém somente os fontes da modificação, um montador mínimo e instruções de build. ROMs, gráficos extraídos, disassembly e resultados gerados não são distribuídos.

## Requisitos

- Python 3.10 ou superior, sem pacotes adicionais.
- Uma cópia local da ferramenta externa `tools/graficos.py`, disponível no [TimePilot-disassembly, de antxiko](https://github.com/antxiko/TimePilot-disassembly). Obtenha esse projeto separadamente e informe seu diretório na build; ele não faz parte deste repositório.
- Sua própria ROM original compatível, de 16.384 bytes, com SHA-256:

```text
183e80262301b18d41762d64a2fc326f4a4bef17832109225637e184d54a70d9
```

Dependência externa verificada no commit `5a998456312ece61b77cf21d5a6fc4823a9ad193` do projeto de referência.

Outras revisões da ROM são recusadas. Não é necessário montar o disassembly: a build usa somente a ferramenta Python externa para interpretar os gráficos da ROM fornecida.

## Gerar a ROM

Execute na raiz deste repositório, ajustando os dois caminhos:

```sh
python tools/build_scroll.py --input "/caminho/timepilot.rom" --disassembly "/caminho/TimePilot-disassembly"
```

No Windows, com Python instalado:

```bat
build.bat --input "C:\jogos\timepilot.rom" --disassembly "C:\fontes\TimePilot-disassembly"
```

O script não baixa ROMs nem dependências. O diretório indicado em `--disassembly` precisa conter `tools/graficos.py`. Use uma cópia obtida do repositório de referência acima.

A saída padrão é `build/timepilot-fino-v7.rom`. Ao lado dela ficam um relatório `.build.json` e um arquivo `.asm` com as novas rotinas. Todos esses resultados são locais e ignorados pelo Git. Use `--output` para escolher outro destino. Não execute Python com `-O`, pois as verificações da build são necessárias.

A ROM gerada tem 32.768 bytes, usa o mapeamento **Page12** no openMSX e deve apresentar o SHA-256:

```text
27be09bdf9cfc0b5860d226f43d4b928490be124fdf9ee0411c4d150a550c435
```

## O que mudou

As imagens das nuvens nas 64 posições finas são calculadas durante a build a partir da ROM do usuário. Durante o jogo, dois grupos de padrões alternam a preparação dos gráficos e a apresentação das nuvens. Acumuladores de meio pixel distribuem os passos dos rumos intermediários, evitando a trajetória em blocos da versão anterior.

Veja [como a modificação foi implementada](docs/IMPLEMENTACAO.md).

## Referência e atribuição

O projeto de referência é o [TimePilot-disassembly](https://github.com/antxiko/TimePilot-disassembly), de antxiko. Seu código e seus arquivos não estão incluídos aqui. A ferramenta externa `graficos.py` permanece sujeita à licença publicada naquele repositório.

Time Pilot e seus gráficos, sons e código original pertencem aos respectivos titulares. Este projeto publica os arquivos necessários para aplicar a modificação localmente; não fornece o jogo original nem a ROM modificada.
