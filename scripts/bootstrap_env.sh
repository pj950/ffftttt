#!/bin/bash

# Bootstrap environment file for Futu Signal Generator

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    echo "⚠️  $ENV_FILE already exists. Skipping creation."
    echo "If you want to recreate it, delete the existing file first."
    exit 0
fi

cat > "$ENV_FILE" << 'EOF'
# Futu OpenD Connection
FUTU_OPEND_HOST=127.0.0.1
FUTU_OPEND_PORT=11111

# Server酱 (Serverchan) Send Key
# Get your key from https://sct.ftqq.com/
SERVERCHAN_KEY=your_serverchan_key_here
EOF

echo "✅ Created $ENV_FILE with placeholder values."
echo ""
echo "📝 Next steps:"
echo "  1. Edit .env and add your actual Futu OpenD host/port"
echo "  2. Add your Server酱 send key from https://sct.ftqq.com/"
echo "  3. Make sure Futu OpenD is running before starting the signal runner"
