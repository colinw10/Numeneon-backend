# 📚 Post-Project Fixes & Learnings

> **Author:** Pablo  
> **Dates:** January 29-30, 2026

This folder documents all the fixes, debugging, and learnings from deploying Numeneon to production (Render + Vercel).

## Contents

| File                                                             | Description                                          |
| ---------------------------------------------------------------- | ---------------------------------------------------- |
| [01-websocket-production-fix.md](01-websocket-production-fix.md) | WebSocket/Redis fix for multi-worker deployment      |
| [02-wall-posts-persistence.md](02-wall-posts-persistence.md)     | target_profile field for wall posts                  |
| [03-post-notifications.md](03-post-notifications.md)             | Real-time notifications when friends post            |
| [04-debugging-techniques.md](04-debugging-techniques.md)         | Tools and techniques used to debug production issues |

## Key Takeaways

1. **InMemoryChannelLayer doesn't work in production** - Always use Redis for WebSockets when deploying with multiple workers
2. **Serializers need explicit field handling** - Just having a model field isn't enough; the serializer must accept and return it
3. **PrimaryKeyRelatedField is powerful** - It handles ForeignKey writes automatically via `source='field_name'`
4. **Django Admin is your friend** - Quick way to verify what's actually in the database
5. **Check Network tab first** - Before debugging backend, verify the frontend is actually making the request

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │     │   Backend       │     │   Database      │
│   (Vercel)      │────▶│   (Render)      │────▶│   (PostgreSQL)  │
│                 │     │                 │     │                 │
│   React         │     │   Django/DRF    │     │   Render DB     │
│   WebSocket     │────▶│   Daphne        │     │                 │
└─────────────────┘     │   Channels      │     └─────────────────┘
                        │        │        │
                        │        ▼        │
                        │   ┌─────────┐   │
                        │   │  Redis  │   │
                        │   │(Upstash)│   │
                        │   └─────────┘   │
                        └─────────────────┘
```
