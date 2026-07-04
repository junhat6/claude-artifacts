# claude-artifacts

Claude Code が生成したアーティファクト（HTML レポート・ドキュメント）を
GitHub Pages で配信するための保管庫。

**公開サイト**: https://junhat6.github.io/claude-artifacts/

> ⚠️ このリポジトリと Pages サイトは**公開**です。
> URL を知っていれば誰でも閲覧できるため、機密情報を含むアーティファクトは置かないこと。

## 使い方

Claude Code のセッション内で `/publish-artifact <HTMLファイルパス>` を実行するか、手動で:

```bash
python3 publish.py path/to/artifact.html
git add -A && git commit -m "Add artifact" && git push
```

`publish.py` がやること:

1. アーティファクト HTML（`<head>` を持たない断片形式）を charset / viewport 付きの
   完全な HTML 文書にラップ — これが無いとモバイル表示が崩れる
2. `YYYY-MM-DD-<slug>.html` のファイル名でリポジトリ直下に配置
3. `index.html`（一覧ページ）を再生成

一覧だけ再生成したい場合は `python3 publish.py --rebuild`。
