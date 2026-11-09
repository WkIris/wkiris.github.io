#!/bin/zsh
cd -- "${0:A:h}" || exit 1
python3 scripts/preview.py --open
if [[ $? -ne 0 ]]; then
  echo "启动失败，请保留窗口中的提示信息。"
  read -r "?按回车关闭窗口"
fi
