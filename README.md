# Time Pilot — Smooth Scroll

[English](#english) | [Português](#português)

## English

A smooth-scrolling patch for Time Pilot (Konami, MSX1), based on the v7 version tested in this project. The build transforms a user-supplied original 16 KB ROM into a 32 KB ROM with one-pixel scrolling and support for all 16 headings.

This repository contains only the modification sources, a minimal assembler, and build instructions. ROMs, extracted graphics, disassembly, and generated output are not distributed.

### Requirements

- Python 3.10 or later, with no additional packages.
- A local copy of the external `tools/graficos.py` tool, available from [antxiko's TimePilot-disassembly](https://github.com/antxiko/TimePilot-disassembly). Obtain that project separately and provide its directory when building; it is not included in this repository.
- Your own compatible original ROM, exactly 16,384 bytes, with this SHA-256:

```text
183e80262301b18d41762d64a2fc326f4a4bef17832109225637e184d54a70d9
```

The external dependency was verified at commit `5a998456312ece61b77cf21d5a6fc4823a9ad193` of the reference project.

Other ROM revisions are rejected. You do not need to assemble the disassembly: the build uses only the external Python tool to interpret the graphics in the supplied ROM.

### Build the ROM

Run from the root of this repository, adjusting both paths:

```sh
python tools/build_scroll.py --input "/path/to/timepilot.rom" --disassembly "/path/to/TimePilot-disassembly"
```

On Windows, with Python installed:

```bat
build.bat --input "C:\games\timepilot.rom" --disassembly "C:\sources\TimePilot-disassembly"
```

The script does not download ROMs or dependencies. The directory passed to `--disassembly` must contain `tools/graficos.py`. Use a copy obtained from the reference repository linked above.

The default output is `build/timepilot-fino-v7.rom`. A `.build.json` report and an `.asm` file containing the new routines are written alongside it. All generated files stay local and are ignored by Git. Use `--output` to choose a different destination. Do not run Python with `-O`, as the build checks must remain enabled.

The generated ROM is 32,768 bytes, uses **Page12** mapping in openMSX, and should have this SHA-256:

```text
27be09bdf9cfc0b5860d226f43d4b928490be124fdf9ee0411c4d150a550c435
```

### What changed

Cloud images for all 64 fine-scroll positions are calculated at build time from the user's ROM. During gameplay, two pattern groups alternate between preparing the graphics and displaying the clouds. Half-pixel accumulators distribute the steps for intermediate headings, avoiding the coarse staircase motion of the previous version.

See the [step-by-step implementation guide](docs/IMPLEMENTACAO.md) (in Portuguese), covering the original scrolling, precomputed patterns, edge cleanup, double buffering, fractional movement, memory layout, and validation.

### Reference and attribution

The reference project is [TimePilot-disassembly](https://github.com/antxiko/TimePilot-disassembly), by antxiko. Its code and files are not included here. The external `graficos.py` tool remains subject to the license published in that repository.

Time Pilot and its graphics, sounds, and original code belong to their respective rights holders. This project publishes the files needed to apply the modification locally; it does not provide the original game or the modified ROM.

---

## Português

Patch de scroll fino para Time Pilot (Konami, MSX1), baseado na versão v7 testada no projeto. A build transforma uma ROM original de 16 KB fornecida pelo usuário em uma ROM de 32 KB, com scroll de um pixel e tratamento dos 16 rumos.

Este repositório contém somente os fontes da modificação, um montador mínimo e instruções de build. ROMs, gráficos extraídos, disassembly e resultados gerados não são distribuídos.

### Requisitos

- Python 3.10 ou superior, sem pacotes adicionais.
- Uma cópia local da ferramenta externa `tools/graficos.py`, disponível no [TimePilot-disassembly, de antxiko](https://github.com/antxiko/TimePilot-disassembly). Obtenha esse projeto separadamente e informe seu diretório na build; ele não faz parte deste repositório.
- Sua própria ROM original compatível, de 16.384 bytes, com SHA-256:

```text
183e80262301b18d41762d64a2fc326f4a4bef17832109225637e184d54a70d9
```

Dependência externa verificada no commit `5a998456312ece61b77cf21d5a6fc4823a9ad193` do projeto de referência.

Outras revisões da ROM são recusadas. Não é necessário montar o disassembly: a build usa somente a ferramenta Python externa para interpretar os gráficos da ROM fornecida.

### Gerar a ROM

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

### O que mudou

As imagens das nuvens nas 64 posições finas são calculadas durante a build a partir da ROM do usuário. Durante o jogo, dois grupos de padrões alternam a preparação dos gráficos e a apresentação das nuvens. Acumuladores de meio pixel distribuem os passos dos rumos intermediários, evitando a trajetória em blocos da versão anterior.

Veja o [guia passo a passo da implementação](docs/IMPLEMENTACAO.md): desenho original, fases pré-calculadas, limpeza de bordas, buffer duplo, movimento fracionário, mapa de memória e validação.

### Referência e atribuição

O projeto de referência é o [TimePilot-disassembly](https://github.com/antxiko/TimePilot-disassembly), de antxiko. Seu código e seus arquivos não estão incluídos aqui. A ferramenta externa `graficos.py` permanece sujeita à licença publicada naquele repositório.

Time Pilot e seus gráficos, sons e código original pertencem aos respectivos titulares. Este projeto publica os arquivos necessários para aplicar a modificação localmente; não fornece o jogo original nem a ROM modificada.
