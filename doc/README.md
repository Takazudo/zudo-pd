# USB-PD Modular Synth Power Documentation

このディレクトリには、USB-PD駆動モジュラーシンセサイザー電源のドキュメントが含まれています。

## セットアップ

```bash
# 依存関係のインストール
pnpm install

# 開発サーバーの起動
pnpm start

# プロダクションビルド
pnpm build
```

## ディレクトリ構造

```
doc/
├── docs/              # ドキュメントのMarkdownファイル
│   └── inbox/         # INBOX カテゴリ
├── src/               # Reactコンポーネントとスタイル
│   ├── css/           # カスタムCSS
│   └── pages/         # カスタムページ
├── static/            # 静的アセット (画像など)
└── plugins/           # カスタムプラグイン
```

## ドキュメントの追加

1. `docs/inbox/` に新しい `.md` ファイルを作成
2. frontmatter を設定:
   ```yaml
   ---
   sidebar_position: 1
   ---
   ```
3. Markdownでコンテンツを記述

## 技術スタック

- [Docusaurus 3](https://docusaurus.io/) - ドキュメントサイトジェネレータ
- [React 19](https://react.dev/) - UIライブラリ
- [TypeScript](https://www.typescriptlang.org/) - 型安全性
- [Mermaid](https://mermaid.js.org/) - ダイアグラム描画

## コマンド

- `pnpm start` - 開発サーバー起動 (http://localhost:3000)
- `pnpm build` - プロダクションビルド
- `pnpm serve` - ビルドしたサイトをローカルで確認
- `pnpm clear` - キャッシュクリア
- `pnpm lint` - コードのリント
- `pnpm format` - コードフォーマット
