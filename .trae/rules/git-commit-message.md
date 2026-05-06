---
alwaysApply: true
scene: git_message
---

# 生成简短、规范、清晰的 Git Commit 信息
# 规则：类型(范围)：描述（≤60字，一句话，简洁有力）
# 不要多余解释，不要多行，不要长句

Rules:
1. 输出**只返回一行** commit message，**不要任何多余内容**
2. 格式必须是：`类型: 简短描述`
3. 类型只能选：feat / fix / docs / style / refactor / test / chore
4. 描述**控制在 50 字符以内**，一句话讲清楚
5. **禁止多行、禁止长段落、禁止解释**
6. 语言保持英文，简洁专业
7. 不要emoji，不要多余符号
8. 只输出最终commit内容，不要任何其他文字