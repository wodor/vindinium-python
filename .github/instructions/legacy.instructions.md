---
applies_to:
  - "app/**"
  - "conf/**"
  - "build.sbt"
  - "project/**"
  - "public/**"
  - "client/**"
---

# Legacy Scala/Play Framework Instructions

⚠️ **DO NOT MODIFY THIS CODE** ⚠️

## Overview

This is the **original Scala/Play Framework implementation** of Vindinium. It is in **maintenance mode only**.

### Status
- **Active Development**: ❌ No
- **Maintenance**: ⚠️ Critical fixes only
- **New Features**: ❌ Never

## Rules

### ❌ DO NOT:
- Add new features to this codebase
- Refactor or modernize this code
- Change dependencies in `build.sbt`
- Modify Play Framework configuration
- Update JavaScript client code
- Make "improvements" or optimizations
- Touch this code unless **explicitly instructed** in your GitHub issue

### ✅ ONLY IF:
- Your GitHub issue **specifically mentions** Scala or Play Framework
- You are fixing a **critical security vulnerability**
- You are instructed to maintain compatibility during migration

## Migration Status

The Vindinium server is being **rewritten in Python 3.11+ with FastAPI**.

- **New Implementation**: `/python/` directory
- **Active Work**: ALL new development happens in Python
- **Your Tasks**: Unless told otherwise, work in `/python/` directory

## If You Need to Understand Legacy Behavior

If your task requires understanding how the original Scala implementation works:

1. ✅ **Read** the Scala code for reference
2. ✅ **Document** behavior in Python specs
3. ✅ **Implement** equivalent functionality in Python
4. ❌ **Do not modify** the Scala code

## File Locations (Read-Only)

- `app/` - Scala Play Framework application code
- `conf/` - Play Framework configuration
- `build.sbt` - SBT build configuration
- `project/` - SBT project configuration
- `public/` - Static assets
- `client/` - JavaScript client code

## Questions?

If your task is unclear about whether to work in Scala or Python:
- **Default assumption**: Work in Python (`/python/` directory)
- **Ask for clarification** if the issue mentions both Scala and Python
- **Check issue labels**: Look for `python`, `scala`, `legacy`, or `migration` labels

## Remember

🐍 **Python is the future** - Focus on `/python/` directory  
🔒 **Scala is frozen** - Read-only unless critical fix  
⛔ **Do not modify legacy code** - It will be replaced
