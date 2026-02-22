#!/bin/bash
# kogisGDP-pages セットアップスクリプト
# 使い方: kogisGDP リポジトリのルートで実行
#   chmod +x setup-pages-repo.sh
#   ./setup-pages-repo.sh

set -e

PAGES_DIR="../kogisGDP-pages"

echo "=== kogisGDP-pages リポジトリをセットアップ ==="

# 1. リポジトリ作成
echo "[1/4] GitHub にリポジトリを作成..."
gh repo create nekyoJap/kogisGDP-pages \
  --public \
  --description "競輪予想ガイド - 公開ページ (kogisGDP)" \
  --clone
cd "$PAGES_DIR"

# 2. 公開ファイルをコピー
echo "[2/4] 公開ファイルをコピー..."

# 静的ページ（docs/ → ルート）
cp ../kogisGDP/docs/index.html .
cp ../kogisGDP/docs/bank.html .
cp ../kogisGDP/docs/race-merge.html .
cp ../kogisGDP/docs/mockup.html .
cp ../kogisGDP/docs/styles.css .
cp ../kogisGDP/docs/race-merge.css .
cp ../kogisGDP/docs/script.js .
cp ../kogisGDP/docs/race-merge.js .

# ガイドページ
cp -r ../kogisGDP/docs/guide .

# RAGナレッジ（一般知識のみ）
mkdir -p data/knowledge
cp ../kogisGDP/data/knowledge/*.md data/knowledge/

# GitHubリンクを新リポに更新
sed -i 's|nekyoJap/kogisGDP"|nekyoJap/kogisGDP-pages"|g' index.html

echo "[3/4] コミット & プッシュ..."
git add -A
git commit -m "初期構築: 競輪予想ガイド公開サイト

kogisGDPから公開コンテンツを分離。

ページ:
- index.html: 予想ボード
- bank.html: バンク予想ボード
- race-merge.html: マージビュー
- mockup.html: プロダクトモックUI
- guide/: 競輪予想ガイド（5カテゴリ）

RAGナレッジ:
- data/knowledge/: 一般的な競輪予想知識"

git push -u origin main

# 3. GitHub Pages 有効化
echo "[4/4] GitHub Pages を有効化..."
gh api repos/nekyoJap/kogisGDP-pages/pages \
  -X POST \
  -f "source[branch]=main" \
  -f "source[path]=/" \
  2>/dev/null && echo "  Pages 有効化完了" || echo "  Pages は手動で Settings > Pages から有効化してください"

echo ""
echo "=== セットアップ完了 ==="
echo "リポジトリ: https://github.com/nekyoJap/kogisGDP-pages"
echo ""
echo "次のステップ:"
echo "  1. kogisGDP を private に変更"
echo "     gh repo edit nekyoJap/kogisGDP --visibility private"
echo "  2. kogisGDP の docs/ を削除（任意）"
echo "     cd ../kogisGDP && git rm -r docs/ && git commit -m 'docs/ を kogisGDP-pages に移管'"
