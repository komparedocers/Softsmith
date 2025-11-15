#!/bin/bash

# Script to help setup local LLM (DeepSeek, Ollama, etc.)

echo "========================================="
echo "  Local LLM Setup Helper"
echo "========================================="
echo ""
echo "This script will help you configure a local LLM."
echo ""
echo "Options:"
echo "  1) Ollama (Recommended - Easy to setup)"
echo "  2) vLLM (Advanced - Better performance)"
echo "  3) Manual configuration"
echo ""
read -p "Select option (1-3): " option

case $option in
    1)
        echo ""
        echo "Setting up Ollama..."
        echo ""
        echo "1. Install Ollama from: https://ollama.ai/"
        echo "2. Run: ollama pull deepseek-coder"
        echo "3. Ollama will serve on: http://localhost:11434"
        echo ""

        cat > configs/config-local-ollama.yaml << 'EOF'
llm:
  mode: "local"
  fallback_enabled: false
  providers:
    openai:
      enabled: false
    claude:
      enabled: false
    local:
      enabled: true
      base_url: "http://host.docker.internal:11434/v1"
      model: "deepseek-coder"
      max_tokens: 4096
      temperature: 0.7
  routing:
    planning: ["local"]
    code_generation: ["local"]
    debugging: ["local"]
    testing: ["local"]
    documentation: ["local"]
    review: ["local"]
EOF

        echo "✓ Created configs/config-local-ollama.yaml"
        echo ""
        echo "To use this configuration:"
        echo "  cp configs/config-local-ollama.yaml configs/config.yaml"
        echo "  ./start.sh"
        ;;

    2)
        echo ""
        echo "Setting up vLLM..."
        echo ""
        echo "1. Install vLLM: pip install vllm"
        echo "2. Run server:"
        echo "   python -m vllm.entrypoints.openai.api_server \\"
        echo "     --model deepseek-ai/deepseek-coder-6.7b-instruct \\"
        echo "     --port 8000"
        echo ""

        cat > configs/config-local-vllm.yaml << 'EOF'
llm:
  mode: "local"
  fallback_enabled: false
  providers:
    openai:
      enabled: false
    claude:
      enabled: false
    local:
      enabled: true
      base_url: "http://host.docker.internal:8000/v1"
      model: "deepseek-ai/deepseek-coder-6.7b-instruct"
      max_tokens: 4096
      temperature: 0.7
  routing:
    planning: ["local"]
    code_generation: ["local"]
    debugging: ["local"]
    testing: ["local"]
    documentation: ["local"]
    review: ["local"]
EOF

        echo "✓ Created configs/config-local-vllm.yaml"
        echo ""
        echo "To use this configuration:"
        echo "  cp configs/config-local-vllm.yaml configs/config.yaml"
        echo "  ./start.sh"
        ;;

    3)
        echo ""
        echo "Manual Configuration:"
        echo ""
        echo "Edit configs/config.yaml and set:"
        echo ""
        echo "llm:"
        echo "  mode: \"local\""
        echo "  providers:"
        echo "    local:"
        echo "      enabled: true"
        echo "      base_url: \"http://your-llm-url:port/v1\""
        echo "      model: \"your-model-name\""
        echo ""
        ;;

    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "  Hybrid Mode (Recommended)"
echo "========================================="
echo ""
echo "For best results, use hybrid mode:"
echo "  - Local LLM for code generation (faster, free)"
echo "  - OpenAI/Claude for planning (better quality)"
echo ""
echo "Edit configs/config.yaml:"
echo ""
cat << 'EOF'
llm:
  mode: "hybrid"
  fallback_enabled: true
  providers:
    openai:
      enabled: true
    local:
      enabled: true
      base_url: "http://host.docker.internal:11434/v1"
      model: "deepseek-coder"
  routing:
    planning: ["openai", "local"]      # Try OpenAI first
    code_generation: ["local", "openai"]  # Try local first
    debugging: ["openai", "local"]
    testing: ["local"]
EOF

echo ""
echo "This gives you the best of both worlds!"
echo ""
