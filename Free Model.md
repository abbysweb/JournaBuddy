Free OpenCode models you can launch directly from PowerShell

Coding (recommended)

opencode --model opencode/deepseek-v4-flash-free

opencode --model opencode/north-mini-code-free

opencode --model opencode/nemotron-3-ultra-free

opencode --model opencode/mimo-v2.5-free

opencode --model opencode/hy3-free

opencode --model opencode/big-pickle


Fast launch with a prompt

opencode --model opencode/deepseek-v4-flash-free "Read my entire repository and explain the architecture."

opencode --model opencode/north-mini-code-free "Review my Python project."

opencode --model opencode/nemotron-3-ultra-free "Explain docker-compose.yml."


Recommended for JournaBuddy

Best overall

opencode --model opencode/deepseek-v4-flash-free

Best code editing

opencode --model opencode/north-mini-code-free

Best long reasoning

opencode --model opencode/nemotron-3-ultra-free

Best lightweight

opencode --model opencode/mimo-v2.5-free


See only free models

PowerShell:

opencode models | Select-String "free|big-pickle|hy3"

or

opencode models | findstr "free big-pickle hy3"

These commands filter the available models to show only the free offerings.