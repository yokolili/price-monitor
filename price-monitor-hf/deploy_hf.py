#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hugging Face Space 一键部署脚本
用途：把 price-monitor-hf/ 目录上传为 HF Space，自动运行

前置条件（用户只需做一次）：
  1. 注册 Hugging Face 账号（仅需邮箱，免手机）：https://huggingface.co/join
  2. 生成 Access Token：https://huggingface.co/settings/tokens
     （选 "Read + Write" 权限，复制 token）
  3. 设置环境变量：export HF_TOKEN="hf_xxxx"  （或在下方直接填）

运行：
  python3 deploy_hf.py --user <你的HF用户名> --repo price-monitor
"""
import os
import sys
import argparse

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    print("缺少依赖，正在安装 huggingface_hub ...")
    os.system("pip3 install -q huggingface_hub")
    from huggingface_hub import HfApi, create_repo


def deploy(hf_user, repo_name, token, local_dir):
    api = HfApi(token=token)
    repo_id = f"{hf_user}/{repo_name}"

    print(f"[1/3] 创建 Space: {repo_id}")
    try:
        create_repo(
            repo_id=repo_id,
            repo_type="space",
            space_sdk="static",
            private=False,
            token=token,
            exist_ok=True,
        )
    except Exception as e:
        print(f"创建 Space 失败：{e}")
        print("请确认：1) token 有 write 权限  2) HF 用户名正确")
        sys.exit(1)

    print(f"[2/3] 上传站点文件: {local_dir}")
    api.upload_folder(
        folder_path=local_dir,
        repo_id=repo_id,
        repo_type="space",
        token=token,
    )

    print(f"[3/3] 部署完成 ✅")
    print(f"    访问地址: https://huggingface.co/spaces/{repo_id}")
    print(f"    首次构建约 1 分钟，之后自动 HTTPS 可访问")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True, help="你的 Hugging Face 用户名")
    parser.add_argument("--repo", default="price-monitor", help="Space 仓库名")
    parser.add_argument("--dir", default=os.path.dirname(os.path.abspath(__file__)),
                        help="本地站点目录（默认脚本所在目录）")
    parser.add_argument("--token", default=os.environ.get("HF_TOKEN"),
                        help="HF Access Token（或用环境变量 HF_TOKEN）")
    args = parser.parse_args()

    if not args.token:
        print("❌ 缺少 HF Token。请设置：")
        print("   export HF_TOKEN='hf_你的token'  或加 --token hf_xxx")
        print("Token 获取：https://huggingface.co/settings/tokens")
        sys.exit(1)

    deploy(args.user, args.repo, args.token, args.dir)


if __name__ == "__main__":
    main()
