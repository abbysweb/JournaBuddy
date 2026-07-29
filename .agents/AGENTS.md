# Agent Execution Rules

1. **Strict Adherence:** The AI must only follow the explicit commands provided by the user. Do not deviate from the requested instructions.
2. **No Hallucinations or Omissions:** Do not invent new features, architectures, or files unless explicitly requested. Do not decrease, remove, or silently omit existing functionality or code without explicit permission.
3. **Ask Before Assuming:** In case of any ambiguity, underspecified requirements, or confusion, STOP and ask the user clarifying questions. Do not make assumptions.
4. **Comprehensive Commenting:** Always add proper, descriptive comments to the code to explain the system's logic and architecture clearly.
5. **Continuous Committing:** After making any updates or completing a set of tasks, automatically stage, commit, and push the changes to GitHub with a descriptive commit message.
