# Memória do BMO

Como o BMO guarda e usa informações sobre você e suas conversas.

---

## Como a Memória Funciona

O BMO tem **memória persistente**: ele lembra de você entre sessões. Quando você diz algo como "Meu time favorito é o Flamengo" ou "Estou trabalhando em um projeto de IA", o BMO guarda essa informação e a utiliza em conversas futuras.

### O que é Lembrado

| Tipo | Exemplo |
|---|---|
| **Fatos** | "Meu nome é Diego", "Moro em São Paulo" |
| **Preferências** | "Gosto de café", "Time favorito: Flamengo" |
| **Projetos** | "Estou criando um assistente de IA" |
| **Contexto** | Informações ditas durante conversas |

---

## Como Ver a Memória

No painel **Memória**, você encontra:

### Seções Categorizadas

- **Fatos conhecidos** 📋 — Informações objetivas sobre você
- **Preferências** ❤️ — Gostos e preferências
- **Projetos** 📁 — Trabalhos e projetos atuais

### Arquivos do Sistema

- **SOUL.md** — Personalidade e regras do BMO (expansível)
- **USER.md** — Perfil do usuário (editável)
- **MEMORY.md** — Registro completo de memórias

---

## Como Adicionar Memória

### Pelo Chat

Simplesmente diga:

> "Meu nome é João"
> "Prefiro Python para programação"
> "Estou trabalhando em um site"
> "Lembre que meu email é joao@email.com"

O BMO detecta automaticamente quando algo é uma informação importante e salva.

### Pelo Painel de Memória

1. Vá em **Memória**
2. Digite no campo de texto
3. Clique em **Salvar**

---

## Como Gerenciar

### Esquecer um Item

- Clique no botão **🗑️** ao lado do item
- Para SOUL.md/USER.md: abra o detalhe e clique em **"Esquecer"**

### Limpar Tudo

1. Vá em **Memória**
2. Clique em **"Limpar memória"**
3. Confirme

### Exportar/Importar Backup

- **Exportar**: Salva toda a memória em um arquivo `.json`
- **Importar**: Restaura um backup anterior

---

## Como a Memória é Armazenada

```
%APPDATA%\bmo\
├── memory\
│   ├── MEMORY.md        ← Memória principal (editável manualmente)
│   ├── SOUL.md          ← Personalidade
│   ├── USER.md          ← Perfil do usuário
│   └── memory.json      ← Backup local
└── workspace\memory\
    ├── MEMORY.md         ← Memória do Nanobot
    ├── SOUL.md           ← Personalidade do Nanobot
    ├── USER.md           ← Perfil do Nanobot
    └── history.jsonl     ← Histórico de conversas
```

> 💡 Você pode editar `SOUL.md` e `USER.md` manualmente para ajustar como o BMO se comporta e o que sabe sobre você.
