#!/usr/bin/env bash
echo "🧹 Wiping installed packages..."
pip freeze | xargs pip uninstall -y
echo "📦 Installing ONLY lean dependencies..."
pip install httpx pydantic fastapi uvicorn
echo "✅ Environment clean!"
