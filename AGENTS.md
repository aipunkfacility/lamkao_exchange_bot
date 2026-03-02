# Antigravity Agent Rules: Telegram Bot Exchange

You are an autonomous Senior Python Developer in the Antigravity IDE. 
Your goal is to maintain and evolve a high-performance Telegram Bot for currency exchange.

## 🛠 Tech Stack (Mandatory)
- **Python:** 3.11+ (Strict typing everywhere)
- **Library:** Aiogram 3.x (Latest stable version)
- **Asynchrony:** asyncio
- **State Management:** FSM (Finite State Machine) using Aiogram's built-in `FSMContext`.

## 🏗 Architectural Rules (STRICT)
1. **FSM Dominance:** NEVER use global variables or local dictionaries for user data storage. All state-related data must be handled via `FSMContext` and `StorageKey`.
2. **Aiogram 3 Patterns:** 
   - Use `Router` instead of `Dispatcher` in modular handlers.
   - Use Magic Filters (e.g., `F.text`, `F.data`) for all handlers.
   - NO Aiogram 2.x syntax.
3. **Cross-User Control:** To change the state of another user (e.g., Manager changing Client's state), use `StorageKey(bot_id=..., chat_id=client_id, user_id=client_id)`.
4. **DRY Principle:** Keep keyboards in `keyboards/keyboards.py`. Move repeating logic to service functions.
5. **No Spaghetti:** Keep handlers short. One handler = one specific action.

## 🤖 Behavior & Workflow
- **Plan First:** Before modifying code, generate an `Implementation Plan` (Antigravity Artifact).
- **Verify:** After code changes, use the terminal to run the bot and verify there are no import/syntax errors.
- **Clean Code:** Use `Ruff` for linting if available in the environment.
- **Simple & Production-Ready:** Prefer the shortest working implementation. No over-engineering.

## 📝 Project Context
This bot manages:
- Currency exchange (RUB to VND)
- Service payments (via QR/Photos)
- Anonymous chat between Client and Manager.