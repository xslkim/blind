#!/bin/bash
# 启动 CosyVoice WebUI
# 用法: bash audio/start_webui.sh

echo "启动 CosyVoice2 WebUI..."
echo "启动后访问: http://localhost:8000"
echo "Ctrl+C 退出"
echo ""

source /home/xsl/miniconda3/etc/profile.d/conda.sh
conda activate cosyvoice
cd /home/xsl/tools/CosyVoice

python webui.py \
  --port 8000 \
  --model_dir pretrained_models/CosyVoice2-0.5B
